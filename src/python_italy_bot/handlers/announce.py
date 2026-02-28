"""Handler for broadcasting announcements to groups."""

import logging
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes

from .. import strings
from ..config import Settings
from ..db.models import Chat
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
                InlineKeyboardButton(text=m.group(1), url=m.group(2)) for m in matches
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


def _parse_target_and_message(raw_announcement: str) -> tuple[str | None, str]:
    """Split 'target | message' into (target, message).

    If no pipe separator is found, returns (None, raw_announcement).
    Only the first pipe is used as delimiter.
    """
    if "|" in raw_announcement:
        target, _, message = raw_announcement.partition("|")
        target = target.strip()
        message = message.strip()
        if target and message:
            return target, message
    return None, raw_announcement


async def _resolve_target_chats(
    target: str,
    moderation_service: ModerationService,
    context: ContextTypes.DEFAULT_TYPE,
) -> list[Chat] | str:
    """Resolve a target string to a list of Chat objects.

    Returns a list of Chat on success, or an error message string on failure.
    Resolution order:
      1. Numeric ID -> direct lookup
      2. @username -> Telegram API get_chat
      3. Otherwise -> search registered chats by title
    """
    # 1. Numeric ID
    if re.match(r"^-?\d+$", target):
        chat_id = int(target)
        # Check if it's a registered chat
        all_chats = await moderation_service.get_all_chats_with_titles()
        for chat in all_chats:
            if chat.chat_id == chat_id:
                return [chat]
        # Not registered but still try to send (owner might know the ID)
        return [Chat(chat_id=chat_id, title=None)]

    # 2. @username -> resolve via Telegram API
    if target.startswith("@"):
        try:
            resolved = await context.bot.get_chat(target)
            return [Chat(chat_id=resolved.id, title=resolved.title)]
        except Exception:
            return strings.ANNOUNCE_GROUP_NOT_FOUND.format(target=target)

    # 3. Search by title
    matches = await moderation_service.find_chats_by_title(target)
    if not matches:
        return strings.ANNOUNCE_GROUP_NOT_FOUND.format(target=target)
    if len(matches) > 1:
        match_lines = "\n".join(f"  {c.chat_id} — {c.title}" for c in matches)
        return strings.ANNOUNCE_AMBIGUOUS_GROUPS.format(
            query=target, matches=match_lines
        )
    return matches


async def _handle_announce(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    moderation_service: ModerationService,
    settings: Settings,
) -> None:
    """Broadcast an announcement to all or a specific group.

    Only works in DM and only for the bot owner.
    Supports HTML formatting and [text](buttonurl://url) button syntax.
    Use pipe syntax to target: /announce target | message
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

    target_str, body = _parse_target_and_message(announcement)

    clean_text, keyboard = _parse_button_urls(body)

    if not clean_text:
        await message.reply_text(strings.ANNOUNCE_EMPTY_MESSAGE)
        return

    # Resolve target chat(s)
    if target_str is not None:
        result = await _resolve_target_chats(target_str, moderation_service, context)
        if isinstance(result, str):
            await message.reply_text(result)
            return
        target_chats = result
        display_name = target_chats[0].title or str(target_chats[0].chat_id)
        await message.reply_text(
            strings.ANNOUNCE_SENDING_TARGETED.format(name=display_name)
        )
        chat_ids = [c.chat_id for c in target_chats]
    else:
        chat_ids = await moderation_service.get_all_chats()
        if not chat_ids:
            await message.reply_text(strings.ANNOUNCE_NO_GROUPS)
            return
        await message.reply_text(strings.ANNOUNCE_SENDING.format(count=len(chat_ids)))

    success = 0
    failed = 0

    for cid in chat_ids:
        try:
            await context.bot.send_message(
                chat_id=cid,
                text=clean_text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            success += 1
        except Exception as e:
            failed += 1
            logger.warning("Failed to send announcement to %s: %s", cid, e)

    await message.reply_text(strings.announce_result(success, failed))


async def _handle_groups(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    moderation_service: ModerationService,
    settings: Settings,
) -> None:
    """List all registered groups. Owner only, private chat only."""
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

    chats = await moderation_service.get_all_chats_with_titles()

    if not chats:
        await message.reply_text(strings.GROUPS_LIST_EMPTY)
        return

    lines = [strings.GROUPS_LIST_HEADER.format(count=len(chats))]
    for c in chats:
        title = c.title or "(senza nome)"
        lines.append(strings.GROUPS_LIST_ROW.format(chat_id=c.chat_id, title=title))

    await message.reply_text("\n".join(lines))


def create_announce_handlers(
    moderation_service: ModerationService, settings: Settings
) -> list[CommandHandler]:
    """Create handlers for the announce and groups commands."""

    async def announce_wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await _handle_announce(update, context, moderation_service, settings)

    async def groups_wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await _handle_groups(update, context, moderation_service, settings)

    return [
        CommandHandler("announce", announce_wrapper),
        CommandHandler("groups", groups_wrapper),
    ]
