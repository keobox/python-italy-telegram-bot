"""Group settings handlers: setwelcome, etc."""

import logging

from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import CommandHandler, ContextTypes

from .. import strings
from ..services.captcha import CaptchaService

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


def create_settings_handlers() -> list:
    """Create group settings handlers."""
    return [
        CommandHandler("setwelcome", _handle_setwelcome),
        CommandHandler("resetwelcome", _handle_resetwelcome),
        CommandHandler("getwelcome", _handle_getwelcome),
    ]


async def _handle_setwelcome(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Set custom welcome message for the group.
    
    Usage: /setwelcome <message>
    
    Supports placeholders:
      - {username}: @username or full name
      - {chatname}: group name
    
    Supports button syntax:
      - [Button Text](buttonurl://URL)
    """
    captcha_service: CaptchaService = context.bot_data["captcha_service"]
    message = update.message
    if message is None or message.from_user is None:
        return

    chat = update.effective_chat
    if chat is None or chat.type == "private":
        await message.reply_text(strings.ONLY_IN_GROUPS)
        return

    if not await _is_admin(context, chat.id, message.from_user.id):
        await message.reply_text(strings.ONLY_ADMINS)
        return

    if message.text is None:
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply_text(strings.SETWELCOME_USAGE)
        return

    welcome_message = parts[1]
    await captcha_service.set_welcome_message(chat.id, welcome_message)
    await message.reply_text(strings.SETWELCOME_SUCCESS)
    logger.info(
        "Welcome message set for chat %s by admin %s",
        chat.id,
        message.from_user.id,
    )


async def _handle_resetwelcome(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Reset welcome message to default."""
    captcha_service: CaptchaService = context.bot_data["captcha_service"]
    message = update.message
    if message is None or message.from_user is None:
        return

    chat = update.effective_chat
    if chat is None or chat.type == "private":
        await message.reply_text(strings.ONLY_IN_GROUPS)
        return

    if not await _is_admin(context, chat.id, message.from_user.id):
        await message.reply_text(strings.ONLY_ADMINS)
        return

    await captcha_service.set_welcome_message(chat.id, None)
    await message.reply_text(strings.RESETWELCOME_SUCCESS)
    logger.info(
        "Welcome message reset for chat %s by admin %s",
        chat.id,
        message.from_user.id,
    )


async def _handle_getwelcome(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Show current welcome message."""
    captcha_service: CaptchaService = context.bot_data["captcha_service"]
    message = update.message
    if message is None or message.from_user is None:
        return

    chat = update.effective_chat
    if chat is None or chat.type == "private":
        await message.reply_text(strings.ONLY_IN_GROUPS)
        return

    if not await _is_admin(context, chat.id, message.from_user.id):
        await message.reply_text(strings.ONLY_ADMINS)
        return

    custom_message = await captcha_service.get_welcome_message(chat.id)
    if custom_message:
        await message.reply_text(
            strings.GETWELCOME_CUSTOM.format(message=custom_message)
        )
    else:
        bot_username = (await context.bot.get_me()).username or "bot"
        default = captcha_service.get_default_welcome_template(bot_username)
        await message.reply_text(
            strings.GETWELCOME_DEFAULT.format(message=default)
        )
