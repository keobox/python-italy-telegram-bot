"""Configuration loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


def _get_env(key: str, default: str | None = None) -> str:
    value = os.environ.get(key, default)
    if value is None:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


def _get_optional_env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


def _get_optional_int(key: str) -> int | None:
    val = os.environ.get(key)
    if val is None or val.strip() == "":
        return None
    try:
        return int(val.strip())
    except ValueError:
        return None


def _get_int_list(key: str) -> list[int]:
    val = os.environ.get(key)
    if val is None or val.strip() == "":
        return []
    return [int(x.strip()) for x in val.split(",") if x.strip()]


class Settings:
    """Bot configuration from environment."""

    def __init__(self) -> None:
        self.telegram_bot_token: str = _get_env("TELEGRAM_BOT_TOKEN")
        self.database_url: str | None = _get_optional_env("DATABASE_URL")
        self.captcha_secret_command: str = _get_optional_env(
            "CAPTCHA_SECRET_COMMAND", "python-italy"
        )
        self.captcha_file_path: str = _get_optional_env(
            "CAPTCHA_FILE_PATH", "assets/regolamento.md"
        )
        self.main_group_id: int | None = _get_optional_int("MAIN_GROUP_ID")
        self.local_group_ids: list[int] = _get_int_list("LOCAL_GROUP_IDS")
        self.rules_url: str | None = _get_optional_env("RULES_URL")
