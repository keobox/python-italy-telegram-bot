"""Spam detection handler."""

import logging

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from ..services.spam_detector import SpamDetector

logger = logging.getLogger(__name__)


def create_spam_handler(spam_detector: SpamDetector) -> MessageHandler:
    """Create the spam detection message handler."""
    return MessageHandler(
        filters.TEXT | filters.CAPTION,
        _handle_message,
    )


async def _handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Check messages for spam and delete if detected."""
    spam_detector: SpamDetector = context.bot_data["spam_detector"]
    message = update.message
    if message is None:
        return

    # Skip private chats
    chat = update.effective_chat
    if chat is None or chat.type == "private":
        return

    result = spam_detector.check(message)
    if not result.is_spam:
        return

    try:
        await message.delete()
        logger.info(
            "Deleted spam from user %s in chat %s: %s",
            message.from_user.id if message.from_user else None,
            chat.id,
            result.reason,
        )
    except Exception as e:
        logger.warning("Could not delete spam message: %s", e)
