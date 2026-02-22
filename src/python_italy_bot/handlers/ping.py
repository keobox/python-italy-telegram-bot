"""Handler for owner-only ping/debug check."""

import logging
import sys
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from .. import strings
from ..config import Settings

logger = logging.getLogger(__name__)


async def _handle_ping(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    settings: Settings,
) -> None:
    """Respond to owner ping with debug info."""
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if settings.bot_owner_id is None or user.id != settings.bot_owner_id:
        return

    bot_info = await context.bot.get_me()
    uptime_info = datetime.now(timezone.utc).isoformat()

    debug_msg = strings.PING_RESPONSE.format(
        bot_username=bot_info.username,
        python_version=sys.version.split()[0],
        timestamp=uptime_info,
    )
    await message.reply_text(debug_msg)


def create_ping_handlers(settings: Settings) -> list[MessageHandler]:
    """Create handlers for owner ping check."""

    async def ping_wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await _handle_ping(update, context, settings)

    return [
        MessageHandler(
            filters.Regex(r"(?i)^electus ci sei\?$") & filters.TEXT,
            ping_wrapper,
        )
    ]
