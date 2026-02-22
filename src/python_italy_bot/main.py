"""Entry point for the Python Italy Telegram Bot."""

import logging

from telegram.ext import ApplicationBuilder

from .config import Settings
from .db import create_repository
from .handlers.moderation import create_moderation_handlers
from .handlers.spam import create_spam_handler
from .handlers.welcome import create_welcome_handlers
from .services.captcha import CaptchaService
from .services.moderation import ModerationService
from .services.spam_detector import SpamDetector

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
    )
    moderation_service = ModerationService(repository)
    spam_detector = SpamDetector()

    application.bot_data["repository"] = repository
    application.bot_data["captcha_service"] = captcha_service
    application.bot_data["moderation_service"] = moderation_service
    application.bot_data["spam_detector"] = spam_detector

    for handler in create_welcome_handlers(captcha_service):
        application.add_handler(handler)
    application.add_handler(create_spam_handler(spam_detector))
    for handler in create_moderation_handlers(moderation_service):
        application.add_handler(handler)


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
