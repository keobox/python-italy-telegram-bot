# Copilot Instructions for python-italy-telegram-bot

## Project Overview

**Electus** is the official Telegram bot for Italian Python community groups.
It handles welcome captcha verification, moderation (ban/mute/report), spam detection, and multi-group management.
Built with `python-telegram-bot` (async), PostgreSQL via `psycopg`, and deployed on Fly.io.

## Tech Stack

- **Language**: Python 3.14+
- **Bot Framework**: python-telegram-bot >= 22.0 (async API)
- **Database**: PostgreSQL via psycopg 3 with async connection pooling; in-memory fallback for dev
- **Config**: python-dotenv for environment variables
- **Build**: Hatchling; dependency management with uv
- **Linting/Formatting**: ruff
- **Type Checking**: mypy
- **Testing**: pytest

## Architecture

Layered architecture with strict separation of concerns:

```
Handlers (telegram.ext)  →  Services (business logic)  →  Repository (data access)
```

- **Handlers** (`src/python_italy_bot/handlers/`): Receive Telegram updates, delegate to services. Each module exposes a `create_*_handlers()` factory that returns a list of `telegram.ext` handler objects.
- **Services** (`src/python_italy_bot/services/`): Contain business logic (`CaptchaService`, `ModerationService`). Depend on `AsyncRepository`.
- **Repository** (`src/python_italy_bot/db/`): Abstract `AsyncRepository` base class with `InMemoryRepository` and `PostgresRepository` implementations. Factory function `create_repository()` selects based on `DATABASE_URL`.
- **Models** (`src/python_italy_bot/db/models.py`): Domain dataclasses (`Ban`, `Mute`, `Report`).
- **Config** (`src/python_italy_bot/config.py`): `Settings` class loads all env vars.
- **Strings** (`src/python_italy_bot/strings.py`): Centralized bot message templates.

Dependency injection is done via `context.bot_data` dictionary, populated in `_post_init`.

## Coding Standards

- **Type hints**: Use modern Python type syntax everywhere (`int | None`, `list[int]`), no `Optional` or `Union`.
- **Async/await**: All handlers, services, and repository methods are `async def`.
- **Docstrings**: Module-level docstring on every file. One-line docstrings on functions and classes.
- **Imports**: Use relative imports within the package (`from ..services.captcha import CaptchaService`).
- **Handler pattern**: Define private `async def _handle_*` functions; expose a public `create_*_handlers()` factory returning `list`.
- **Error handling**: Wrap Telegram API calls in `try/except`, log warnings, degrade gracefully.
- **Logging**: Use `logging.getLogger(__name__)` per module.
- **String formatting**: Use f-strings or `.format()` with named placeholders from `strings.py`.
- **No global mutable state**: Pass dependencies through services and `bot_data`.

## Testing Rules

- Use `pytest` with async support for testing async code.
- Test services and repository implementations independently.
- Use `InMemoryRepository` for unit tests instead of mocking the database.
- Keep tests in the `tests/` directory mirroring the `src/` structure.

## Common Pitfalls

- **Permissions**: Always check that the bot has admin permissions before calling `restrict_chat_member` or `ban_chat_member`.
- **Null checks**: `update.effective_chat`, `update.effective_user`, and `update.message` can all be `None`; guard every handler.
- **Global vs per-chat**: Verification and bans operate globally across all tracked chats. Use `register_chat()` to track new chats.
- **Connection pool**: `PostgresRepository` uses `psycopg_pool.AsyncConnectionPool`; always access connections via `async with self._pool.connection()`.
- **Environment variables**: Required vars raise `ValueError` if missing. Optional vars default to `None`. See `.env.example` for the full list.
- **Bot messages are in Italian**: Keep all user-facing strings in `strings.py` in Italian.
