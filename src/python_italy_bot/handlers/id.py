"""ID handler: returns chat and user IDs."""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes


def create_id_handlers() -> list:
    """Create the /id command handler."""
    return [CommandHandler("id", _handle_id)]


async def _handle_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply with the current chat ID and user ID."""
    chat = update.effective_chat
    user = update.effective_user
    message = update.message

    if chat is None or user is None or message is None:
        return

    await message.reply_text(f"ID chat: {chat.id}\nID utente: {user.id}")
