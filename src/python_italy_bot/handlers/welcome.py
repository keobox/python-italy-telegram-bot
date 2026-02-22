"""Welcome and captcha handlers for new members."""

import logging

from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import ChatMemberHandler, ContextTypes, MessageHandler, filters

from ..services.captcha import CaptchaService

logger = logging.getLogger(__name__)


def create_welcome_handlers(captcha_service: CaptchaService) -> list:
    """Create welcome and captcha handlers."""
    return [
        ChatMemberHandler(
            _handle_new_member,
            ChatMemberHandler.CHAT_MEMBER,
        ),
        MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE,
            _handle_private_message,
        ),
    ]


async def _handle_new_member(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle new chat members: restrict and send welcome with captcha instructions."""
    captcha_service: CaptchaService = context.bot_data["captcha_service"]
    result = update.chat_member
    if result is None:
        return

    new_status = result.new_chat_member.status
    old_status = result.old_chat_member.status if result.old_chat_member else None

    # Only handle new joins (not status changes from restricted to member, etc.)
    if new_status not in (ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED):
        return
    if old_status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
    ):
        return

    user = result.new_chat_member.user
    chat = update.effective_chat
    if user is None or chat is None:
        return

    # Skip if bot
    if user.is_bot:
        return

    # Skip if already verified
    if await captcha_service.is_verified(user.id, chat.id):
        return

    # Restrict new member
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=user.id,
            permissions=captcha_service.get_restricted_permissions(),
        )
    except Exception as e:
        logger.warning("Could not restrict user %s in chat %s: %s", user.id, chat.id, e)
        return

    # Record pending verification
    await captcha_service.add_pending(user.id, chat.id)

    # Send welcome message
    welcome = captcha_service.get_welcome_message()
    try:
        await context.bot.send_message(
            chat_id=chat.id,
            text=welcome,
        )
    except Exception as e:
        logger.warning("Could not send welcome to chat %s: %s", chat.id, e)


async def _handle_private_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle private messages: check for secret command and verify user."""
    captcha_service: CaptchaService = context.bot_data["captcha_service"]
    message = update.message
    if message is None or message.text is None:
        return

    user = update.effective_user
    if user is None:
        return

    if not captcha_service.is_secret_command(message.text):
        await message.reply_text(
            "Comando non riconosciuto. Leggi il file delle regole del gruppo "
            "e invia il comando segreto che troverai."
        )
        return

    pending_chats = await captcha_service.get_pending_chats(user.id)
    if not pending_chats:
        await message.reply_text(
            "Sei già verificato oppure non hai gruppi in attesa. "
            "Se hai appena fatto il captcha, potrebbe essere già stato applicato."
        )
        return

    for chat_id in pending_chats:
        await captcha_service.verify_user(user.id, chat_id)
        try:
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user.id,
                permissions=captcha_service.get_full_permissions(),
            )
        except Exception as e:
            logger.warning(
                "Could not unrestrict user %s in chat %s: %s", user.id, chat_id, e
            )

    await message.reply_text(
        "Verifica completata! Ora puoi partecipare alle discussioni nei gruppi Python Italia."
    )
