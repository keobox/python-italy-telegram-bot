"""Handler for broadcasting announcements to all groups."""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes

from .. import strings
from ..config import Settings
from ..services.captcha import BUTTON_URL_PATTERN
from ..services.moderation import ModerationService

logger = logging.getLogger(__name__)


def _parse_button_urls(text: str) -> tuple[str, InlineKeyboardMarkup | None]:
    """Extract buttonurl:// patterns and build InlineKeyboardMarkup.

    Returns (clean_text, keyboard) where clean_text has button syntax removed.
    Multiple buttons on the same line become the same row.
    """
    lines = text.split("\n")
    keyboard_rows: list[list[InlineKeyboardButton]] = []
    clean_lines: list[str] = []

    for line in lines:
        matches = list(BUTTON_URL_PATTERN.finditer(line))
        if matches:
            row = [
                InlineKeyboardButton(text=m.group(1), url=m.group(2))
                for m in matches
            ]
            keyboard_rows.append(row)
            clean_line = BUTTON_URL_PATTERN.sub("", line).strip()
            if clean_line:
                clean_lines.append(clean_line)
        else:
            clean_lines.append(line)

    clean_text = "\n".join(clean_lines).strip()
    keyboard = InlineKeyboardMarkup(keyboard_rows) if keyboard_rows else None
    return clean_text, keyboard


async def _handle_announce(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    moderation_service: ModerationService,
    settings: Settings,
) -> None:
    """Broadcast an announcement to all registered groups.

    Only works in DM and only for the bot owner.
    Supports HTML formatting and [text](buttonurl://url) button syntax.
    """
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not message or not chat or not user:
        return

    if chat.type != "private":
        await message.reply_text(strings.ONLY_IN_PRIVATE)
        return

    if settings.bot_owner_id is None:
        await message.reply_text(strings.ANNOUNCE_NO_OWNER_CONFIGURED)
        return

    if user.id != settings.bot_owner_id:
        await message.reply_text(strings.ANNOUNCE_OWNER_ONLY)
        return

    raw_text = message.text or ""
    announcement = raw_text.partition(" ")[2].strip()

    if not announcement:
        await message.reply_text(strings.ANNOUNCE_USAGE)
        return

    clean_text, keyboard = _parse_button_urls(announcement)

    if not clean_text:
        await message.reply_text(strings.ANNOUNCE_EMPTY_MESSAGE)
        return

    chat_ids = await moderation_service.get_all_chats()

    if not chat_ids:
        await message.reply_text(strings.ANNOUNCE_NO_GROUPS)
        return

    await message.reply_text(strings.ANNOUNCE_SENDING.format(count=len(chat_ids)))

    success = 0
    failed = 0

    for chat_id in chat_ids:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=clean_text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            success += 1
        except Exception as e:
            failed += 1
            logger.warning("Failed to send announcement to %s: %s", chat_id, e)

    await message.reply_text(strings.announce_result(success, failed))


def create_announce_handlers(
    moderation_service: ModerationService, settings: Settings
) -> list[CommandHandler]:
    """Create handlers for the announce command."""

    async def announce_wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await _handle_announce(update, context, moderation_service, settings)

    return [CommandHandler("announce", announce_wrapper)]
