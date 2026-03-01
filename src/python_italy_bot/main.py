"""Entry point for the Python Italy Telegram Bot."""

import logging
from datetime import datetime, timezone

from telegram.ext import ApplicationBuilder

from .config import Settings
from .db import create_repository
from .handlers.announce import create_announce_handlers
from .handlers.id import create_id_handlers
from .handlers.moderation import create_moderation_handlers
from .handlers.ping import create_ping_handlers
from .handlers.settings import create_settings_handlers

# from .handlers.spam import create_spam_handler
from .handlers.utils import create_user_tracking_handler
from .handlers.welcome import (
    DEFAULT_WELCOME_DELAY_MINUTES,
    _delete_welcome_message,
    create_welcome_handlers,
)
from .services.captcha import CaptchaService
from .services.moderation import ModerationService
# from .services.spam_detector import SpamDetector

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def _post_init(application) -> None:
    """Initialize services and register handlers."""
    settings = application.bot_data["settings"]
    repository = await create_repository(settings.database_url)

    captcha_service = CaptchaService(
        repository,
        secret_command=settings.captcha_secret_command,
        file_path=settings.captcha_file_path,
        rules_url=settings.rules_url,
    )
    moderation_service = ModerationService(repository)
    # spam_detector = SpamDetector()

    application.bot_data["repository"] = repository
    application.bot_data["captcha_service"] = captcha_service
    application.bot_data["moderation_service"] = moderation_service
    # application.bot_data["spam_detector"] = spam_detector

    # Register user-tracking middleware before all other handlers (group -1)
    application.add_handler(create_user_tracking_handler(), group=-1)

    for handler in create_id_handlers():
        application.add_handler(handler)
    for handler in create_settings_handlers():
        application.add_handler(handler)
    for handler in create_moderation_handlers(moderation_service):
        application.add_handler(handler)
    for handler in create_welcome_handlers(captcha_service):
        application.add_handler(handler)
    for handler in create_announce_handlers(moderation_service, settings):
        application.add_handler(handler)
    for handler in create_ping_handlers(settings):
        application.add_handler(handler)
    # application.add_handler(create_spam_handler(spam_detector))

    # Re-schedule deletion for welcome messages persisted before a restart
    await _reschedule_welcome_deletions(application, captcha_service)


async def _reschedule_welcome_deletions(
    application, captcha_service: CaptchaService
) -> None:
    """Re-schedule deletion jobs for welcome messages that survived a bot restart."""
    job_queue = application.job_queue
    if job_queue is None:
        return

    messages = await captcha_service.get_all_welcome_messages()
    if not messages:
        return

    now = datetime.now(timezone.utc)
    welcome_map = application.bot_data.setdefault("welcome_message_map", {})
    scheduled = 0

    for chat_id, message_id, user_id, created_at in messages:
        # Restore in-memory mapping for ban-by-reply
        welcome_map[(chat_id, message_id)] = user_id

        delay_minutes = await captcha_service.get_welcome_delay(chat_id)
        if delay_minutes is None:
            delay_minutes = DEFAULT_WELCOME_DELAY_MINUTES
        if delay_minutes <= 0:
            continue

        # Calculate remaining time; delete immediately if overdue
        elapsed = (now - created_at).total_seconds()
        remaining = max(delay_minutes * 60 - elapsed, 0)

        job_queue.run_once(
            _delete_welcome_message,
            when=remaining,
            data=(chat_id, message_id),
            name=f"del_welcome_{chat_id}_{message_id}",
        )
        scheduled += 1

    if scheduled:
        logger.info("Re-scheduled deletion for %d welcome message(s)", scheduled)


async def _post_shutdown(application) -> None:
    """Clean up resources on shutdown."""
    repository = application.bot_data.get("repository")
    if repository and hasattr(repository, "close"):
        await repository.close()
        logger.info("Database connection closed")


def main() -> None:
    """Run the bot."""
    settings = Settings()
    application = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )
    application.bot_data["settings"] = settings
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=["message", "chat_member"])


if __name__ == "__main__":
    main()
