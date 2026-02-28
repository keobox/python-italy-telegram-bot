"""Shared utilities for all handlers."""

import logging

from telegram import Update
from telegram.ext import ContextTypes, TypeHandler

from ..db.base import AsyncRepository

logger = logging.getLogger(__name__)


async def track_user(repo: AsyncRepository, user: object) -> None:
    """Track a Telegram user in the known_users table."""
    await repo.upsert_known_user(
        user_id=user.id,  # type: ignore[attr-defined]
        username=getattr(user, "username", None),
        first_name=getattr(user, "first_name", None),
        last_name=getattr(user, "last_name", None),
    )


async def _handle_track_user(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Middleware: track the effective user for every update."""
    user = update.effective_user
    if user is None:
        return
    repository: AsyncRepository | None = context.bot_data.get("repository")
    if repository is None:
        return
    try:
        await track_user(repository, user)
    except Exception as e:
        logger.warning("Failed to track user %s: %s", user.id, e, exc_info=True)


def create_user_tracking_handler() -> TypeHandler:
    """Create a TypeHandler that tracks users from every incoming update."""
    return TypeHandler(Update, _handle_track_user)
