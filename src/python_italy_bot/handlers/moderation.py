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
        CommandHandler("forcegroupregistration", _handle_force_group_registration),
    ]


async def _handle_force_group_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Force registration of current chat in bot_chats table. Admin only."""
    moderation_service: ModerationService = context.bot_data["moderation_service"]
    message = update.message
    if message is None or message.from_user is None:
        return

    chat = update.effective_chat
    if chat is None or chat.type == "private":
        await message.reply_text("Questo comando funziona solo nei gruppi.")
        return

    if not await _is_admin(context, chat.id, message.from_user.id):
        await message.reply_text(
            "Solo gli amministratori possono usare questo comando."
        )
        return

    await moderation_service.register_chat(chat.id)
    await message.reply_text(f"Gruppo registrato. Chat ID: {chat.id}")


async def _handle_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ban a user globally. Usage: /ban user_id [reason] or reply to message with /ban [reason]"""
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
        reason = " ".join(args) if args else None
    elif args:
        target = args[0]
        reason = args[1] if len(args) > 1 else None
        user_id = await _resolve_user_id(context, chat.id, target)

    if user_id is None:
        await message.reply_text(
            "Uso: /ban user_id [motivo], o rispondi al messaggio con /ban [motivo]."
        )
        return

    chat_ids = await moderation_service.add_global_ban(
        user_id, message.from_user.id, reason
    )

    success_count = 0
    fail_count = 0
    for cid in chat_ids:
        try:
            await context.bot.ban_chat_member(cid, user_id)
            success_count += 1
        except Exception as e:
            logger.debug("Ban in chat %s failed: %s", cid, e)
            fail_count += 1

    msg = f"Utente bannato globalmente in {success_count} gruppi."
    if fail_count > 0:
        msg += f" ({fail_count} falliti)"
    msg += f"\nMotivo: {reason or 'Nessuno'}"
    await message.reply_text(msg)


async def _handle_unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unban a user globally. Usage: /unban user_id or reply to message with /unban"""
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
            "Uso: /unban user_id, o rispondi al messaggio con /unban"
        )
        return

    chat_ids = await moderation_service.remove_global_ban(user_id)

    success_count = 0
    fail_count = 0
    for cid in chat_ids:
        try:
            await context.bot.unban_chat_member(cid, user_id)
            success_count += 1
        except Exception as e:
            logger.debug("Unban in chat %s failed: %s", cid, e)
            fail_count += 1

    msg = f"Utente sbannato globalmente da {success_count} gruppi."
    if fail_count > 0:
        msg += f" ({fail_count} falliti)"
    await message.reply_text(msg)


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
    reported_user = None

    if message.reply_to_message and message.reply_to_message.from_user:
        reported_user = message.reply_to_message.from_user
        reported_user_id = reported_user.id
        message_id = message.reply_to_message.message_id

    if reported_user_id is None or reported_user is None:
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

    await _notify_admins_of_report(
        context=context,
        chat=chat,
        reporter=message.from_user,
        reported_user=reported_user,
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


def _get_user_display_name(user) -> str:
    """Get display name for a user (full name or username)."""
    if user.first_name:
        name = user.first_name
        if user.last_name:
            name += f" {user.last_name}"
        return name
    return user.username or str(user.id)


def _build_message_link(chat, message_id: int | None) -> str | None:
    """Build a link to a message in a chat."""
    if message_id is None:
        return None
    if chat.username:
        return f"https://t.me/{chat.username}/{message_id}"
    chat_id_str = str(chat.id)
    if chat_id_str.startswith("-100"):
        chat_id_str = chat_id_str[4:]
    return f"https://t.me/c/{chat_id_str}/{message_id}"


async def _notify_admins_of_report(
    context: ContextTypes.DEFAULT_TYPE,
    chat,
    reporter,
    reported_user,
    message_id: int | None,
    reason: str | None,
) -> None:
    """Send report notification to all chat admins via private message."""
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
    except Exception as e:
        logger.warning("Failed to get admins for report notification: %s", e)
        return

    chat_title = chat.title or "Chat"
    reporter_name = _get_user_display_name(reporter)
    reported_name = _get_user_display_name(reported_user)
    message_link = _build_message_link(chat, message_id)

    report_text = f"<b>{chat_title}:</b>\n"
    report_text += f'Reported user: <a href="tg://user?id={reported_user.id}">{reported_name}</a> ({reported_user.id})\n'
    report_text += f'Reported by: <a href="tg://user?id={reporter.id}">{reporter_name}</a> ({reporter.id})\n'
    if message_link:
        report_text += f'Link: <a href="{message_link}">qui</a>\n'
    if reason:
        report_text += f"Reason: {reason}"

    for admin in admins:
        if admin.user.is_bot:
            continue
        try:
            await context.bot.send_message(
                chat_id=admin.user.id,
                text=report_text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.debug(
                "Could not send report to admin %s: %s", admin.user.id, e
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
