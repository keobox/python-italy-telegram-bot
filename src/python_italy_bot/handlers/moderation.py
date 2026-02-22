"""Moderation handlers: ban, mute, report."""

import logging
import re

from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import CommandHandler, ContextTypes

from ..services.moderation import ModerationService

logger = logging.getLogger(__name__)


async def _is_admin(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int
) -> bool:
    """Check if user is admin in the chat."""
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except Exception:
        return False


def create_moderation_handlers(moderation_service: ModerationService) -> list:
    """Create ban, mute, and report handlers."""
    return [
        CommandHandler("ban", _handle_ban),
        CommandHandler("unban", _handle_unban),
        CommandHandler("mute", _handle_mute),
        CommandHandler("unmute", _handle_unmute),
        CommandHandler("report", _handle_report),
    ]


async def _handle_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ban a user. Usage: /ban @username or /ban user_id [reason] or reply to message with /ban [reason]"""
    moderation_service: ModerationService = context.bot_data["moderation_service"]
    message = update.message
    if message is None or message.from_user is None:
        return

    chat = update.effective_chat
    if chat is None or chat.type == "private":
        return

    if not await _is_admin(context, chat.id, message.from_user.id):
        await message.reply_text(
            "Solo gli amministratori possono usare questo comando."
        )
        return

    args = message.text.split(maxsplit=2)[1:] if message.text else []

    user_id: int | None = None
    reason: str | None = None
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
        reason = args[0] if args else None
    elif args:
        target = args[0]
        reason = args[1] if len(args) > 1 else None
        user_id = await _resolve_user_id(context, chat.id, target)

    if user_id is None:
        await message.reply_text(
            "Uso: /ban @username, /ban user_id [motivo], o rispondi al messaggio con /ban [motivo]. "
            "Per @username funziona solo con amministratori."
        )
        return

    try:
        await context.bot.ban_chat_member(chat.id, user_id)
        await moderation_service.add_ban(user_id, chat.id, message.from_user.id, reason)
        await message.reply_text(f"Utente bannato. Motivo: {reason or 'Nessuno'}")
    except Exception as e:
        logger.warning("Ban failed: %s", e)
        await message.reply_text("Impossibile bannare l'utente.")


async def _handle_unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unban a user. Usage: /unban @username or /unban user_id"""
    moderation_service: ModerationService = context.bot_data["moderation_service"]
    message = update.message
    if message is None or message.from_user is None:
        return

    chat = update.effective_chat
    if chat is None or chat.type == "private":
        return

    if not await _is_admin(context, chat.id, message.from_user.id):
        await message.reply_text(
            "Solo gli amministratori possono usare questo comando."
        )
        return

    args = message.text.split(maxsplit=1)[1:] if message.text else []
    user_id: int | None = None
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    elif args:
        user_id = await _resolve_user_id(context, chat.id, args[0])

    if user_id is None:
        await message.reply_text(
            "Uso: /unban @username, /unban user_id, o rispondi al messaggio"
        )
    if user_id is None:
        await message.reply_text("Utente non trovato.")
        return

    try:
        await context.bot.unban_chat_member(chat.id, user_id)
        await moderation_service.remove_ban(user_id, chat.id)
        await message.reply_text("Utente sbannato.")
    except Exception as e:
        logger.warning("Unban failed: %s", e)
        await message.reply_text("Impossibile sbannare l'utente.")


async def _handle_mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mute a user. Usage: /mute @username [duration_minutes] [reason]"""
    moderation_service: ModerationService = context.bot_data["moderation_service"]
    message = update.message
    if message is None or message.from_user is None:
        return

    chat = update.effective_chat
    if chat is None or chat.type == "private":
        return

    if not await _is_admin(context, chat.id, message.from_user.id):
        await message.reply_text(
            "Solo gli amministratori possono usare questo comando."
        )
        return

    args = message.text.split(maxsplit=3)[1:] if message.text else []
    user_id: int | None = None
    duration: int | None = None
    reason: str | None = None

    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
        if args:
            if args[0].isdigit():
                duration = int(args[0])
                reason = args[1] if len(args) > 1 else None
            else:
                reason = args[0]
    elif args:
        target = args[0]
        if len(args) > 1 and args[1].isdigit():
            duration = int(args[1])
            reason = args[2] if len(args) > 2 else None
        else:
            reason = args[1] if len(args) > 1 else None
        user_id = await _resolve_user_id(context, chat.id, target)

    if user_id is None:
        await message.reply_text(
            "Uso: /mute @username [minuti] [motivo], o rispondi al messaggio"
        )
    if user_id is None:
        await message.reply_text("Utente non trovato.")
        return

    until = None
    if duration is not None and duration > 0:
        from datetime import datetime, timezone

        until = int((datetime.now(timezone.utc).timestamp()) + duration * 60)

    try:
        await context.bot.restrict_chat_member(
            chat.id,
            user_id,
            moderation_service.get_mute_permissions(),
            until_date=until,
        )
        await moderation_service.add_mute(
            user_id,
            chat.id,
            message.from_user.id,
            reason=reason,
            until=until,
        )
        msg = "Utente mutato"
        if duration:
            msg += f" per {duration} minuti"
        if reason:
            msg += f". Motivo: {reason}"
        await message.reply_text(msg)
    except Exception as e:
        logger.warning("Mute failed: %s", e)
        await message.reply_text("Impossibile mutare l'utente.")


async def _handle_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unmute a user. Usage: /unmute @username"""
    moderation_service: ModerationService = context.bot_data["moderation_service"]
    message = update.message
    if message is None or message.from_user is None:
        return

    chat = update.effective_chat
    if chat is None or chat.type == "private":
        return

    if not await _is_admin(context, chat.id, message.from_user.id):
        await message.reply_text(
            "Solo gli amministratori possono usare questo comando."
        )
        return

    args = message.text.split(maxsplit=1)[1:] if message.text else []
    user_id: int | None = None
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    elif args:
        user_id = await _resolve_user_id(context, chat.id, args[0])

    if user_id is None:
        await message.reply_text(
            "Uso: /unmute @username, /unmute user_id, o rispondi al messaggio"
        )
    if user_id is None:
        await message.reply_text("Utente non trovato.")
        return

    from telegram import ChatPermissions

    full_perms = ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_change_info=False,
        can_invite_users=True,
        can_pin_messages=False,
    )

    try:
        await context.bot.restrict_chat_member(chat.id, user_id, full_perms)
        await moderation_service.remove_mute(user_id, chat.id)
        await message.reply_text("Utente smutato.")
    except Exception as e:
        logger.warning("Unmute failed: %s", e)
        await message.reply_text("Impossibile smutare l'utente.")


async def _handle_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Report a message or user. Usage: /report [reason] or reply to message with /report [reason]"""
    moderation_service: ModerationService = context.bot_data["moderation_service"]
    message = update.message
    if message is None or message.from_user is None:
        return

    chat = update.effective_chat
    if chat is None or chat.type == "private":
        return

    args = message.text.split(maxsplit=1)[1:] if message.text else []
    reason = args[0] if args else None

    reported_user_id: int | None = None
    message_id: int | None = None

    if message.reply_to_message and message.reply_to_message.from_user:
        reported_user_id = message.reply_to_message.from_user.id
        message_id = message.reply_to_message.message_id

    if reported_user_id is None:
        await message.reply_text(
            "Rispondi al messaggio da segnalare con /report [motivo]"
        )
        return

    await moderation_service.add_report(
        reporter_id=message.from_user.id,
        reported_user_id=reported_user_id,
        chat_id=chat.id,
        message_id=message_id,
        reason=reason,
    )

    await message.reply_text(
        "Segnalazione inviata. Gli amministratori la esamineranno."
    )
    logger.info(
        "Report: %s reported %s in chat %s",
        message.from_user.id,
        reported_user_id,
        chat.id,
    )


async def _resolve_user_id(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    target: str,
) -> int | None:
    """Resolve @username or user_id to numeric user_id. @username only works for admins."""
    target = target.strip()
    if target.startswith("@"):
        try:
            admins = await context.bot.get_chat_administrators(chat_id)
            username_lower = target.lstrip("@").lower()
            for admin in admins:
                if (
                    admin.user.username
                    and admin.user.username.lower() == username_lower
                ):
                    return admin.user.id
            return None
        except Exception:
            return None
    if re.match(r"^-?\d+$", target):
        return int(target)
    return None
