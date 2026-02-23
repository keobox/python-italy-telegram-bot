# CLAUDE.md — Project Specification for python-italy-telegram-bot

<project>
  <name>python-italy-telegram-bot (Electus)</name>
  <description>
    Official Telegram bot for the Italian Python community groups.
    Handles welcome captcha verification, moderation (ban/mute/report),
    spam detection, and multi-group management.
  </description>
  <language>Python 3.14+</language>
  <license>MIT</license>
</project>

<tech_stack>
  <runtime>Python 3.14+ (async/await throughout)</runtime>
  <framework>python-telegram-bot >= 22.0 (async API via telegram.ext)</framework>
  <database>PostgreSQL via psycopg 3 with AsyncConnectionPool; InMemoryRepository fallback</database>
  <config>python-dotenv for environment variables</config>
  <build>Hatchling build backend; uv for dependency management</build>
  <deployment>Docker multi-stage build; deployed on Fly.io (polling mode)</deployment>
  <linting>ruff (linter and formatter)</linting>
  <type_checking>mypy</type_checking>
  <testing>pytest</testing>
</tech_stack>

<architecture>
  <overview>
    Layered architecture: Handlers → Services → Repository → Database.
    Dependency injection via context.bot_data dictionary populated at startup.
  </overview>

  <layer name="handlers" path="src/python_italy_bot/handlers/">
    Receive Telegram updates and delegate to services.
    Each module exposes a create_*_handlers() factory returning a list of telegram.ext handler objects.
    Private async handler functions follow the _handle_* naming convention.
    Modules: welcome.py, moderation.py, spam.py, settings.py, id.py, announce.py, ping.py.
  </layer>

  <layer name="services" path="src/python_italy_bot/services/">
    Business logic layer. Classes: CaptchaService, ModerationService, SpamDetector.
    Depend on AsyncRepository for persistence. Stateless except for repository reference.
  </layer>

  <layer name="repository" path="src/python_italy_bot/db/">
    Abstract AsyncRepository base class (db/base.py) with two implementations:
    - InMemoryRepository (db/in_memory.py) — for development and testing
    - PostgresRepository (db/postgres.py) — production with psycopg AsyncConnectionPool
    Factory function create_repository() in db/__init__.py selects implementation based on DATABASE_URL.
    Domain models (Ban, Mute, Report) are dataclasses in db/models.py.
  </layer>

  <layer name="config" path="src/python_italy_bot/config.py">
    Settings class loads environment variables. Required vars raise ValueError if missing.
    See .env.example for the full list of configuration options.
  </layer>

  <layer name="strings" path="src/python_italy_bot/strings.py">
    All user-facing bot messages centralized here, in Italian.
    Uses named placeholders for .format() substitution.
  </layer>

  <layer name="entry_point" path="src/python_italy_bot/main.py">
    Creates ApplicationBuilder, registers handlers via _post_init callback,
    initializes repository and services, runs polling loop.
  </layer>
</architecture>

<coding_conventions>
  <rule name="type_hints">
    Use modern Python type syntax: int | None, list[int], dict[str, Any].
    Do not use Optional or Union from typing.
  </rule>
  <rule name="async">
    All handlers, service methods, and repository methods must be async def.
  </rule>
  <rule name="docstrings">
    Every file has a module-level docstring. Functions and classes have one-line docstrings.
  </rule>
  <rule name="imports">
    Use relative imports within the package (from ..services.captcha import CaptchaService).
  </rule>
  <rule name="handler_pattern">
    Define private async _handle_* functions. Expose a public create_*_handlers() factory returning list.
  </rule>
  <rule name="error_handling">
    Wrap Telegram API calls in try/except, log warnings with logger, degrade gracefully.
  </rule>
  <rule name="logging">
    Use logging.getLogger(__name__) per module.
  </rule>
  <rule name="strings">
    All user-facing text lives in strings.py in Italian. Use named placeholders.
  </rule>
  <rule name="no_global_state">
    No global mutable state. Pass dependencies through services and bot_data.
  </rule>
</coding_conventions>

<commands>
  <command name="install">uv sync --dev</command>
  <command name="run">uv run python-italy-bot</command>
  <command name="lint">uv run ruff check src/</command>
  <command name="format">uv run ruff format src/</command>
  <command name="typecheck">uv run mypy src/</command>
  <command name="test">uv run pytest</command>
</commands>

<testing>
  <framework>pytest with async support</framework>
  <directory>tests/</directory>
  <guidelines>
    - Test services and repository implementations independently.
    - Use InMemoryRepository for unit tests; do not mock the database interface.
    - Mirror the src/ directory structure in tests/.
    - Keep tests focused and avoid testing Telegram API internals.
  </guidelines>
</testing>

<environment>
  <variable name="TELEGRAM_BOT_TOKEN" required="true">Bot token from @BotFather</variable>
  <variable name="DATABASE_URL" required="false">PostgreSQL connection string; omit for in-memory</variable>
  <variable name="CAPTCHA_SECRET_COMMAND" required="false" default="python-italy">Secret command for captcha verification</variable>
  <variable name="CAPTCHA_FILE_PATH" required="false" default="assets/regolamento.md">Path to rules file</variable>
  <variable name="MAIN_GROUP_ID" required="false">Main group chat ID</variable>
  <variable name="LOCAL_GROUP_IDS" required="false">Comma-separated local group IDs</variable>
  <variable name="RULES_URL" required="false">External rules page URL</variable>
  <variable name="BOT_OWNER_ID" required="false">Owner user ID for /announce</variable>
</environment>

<pitfalls>
  <pitfall>Always guard against None for update.effective_chat, update.effective_user, and update.message.</pitfall>
  <pitfall>Verification and bans are global across all tracked chats. Use register_chat() for new chats.</pitfall>
  <pitfall>PostgresRepository requires async with self._pool.connection() for all DB access.</pitfall>
  <pitfall>Bot must have admin permissions to restrict or ban members.</pitfall>
  <pitfall>Bot messages are in Italian — keep strings.py consistent.</pitfall>
</pitfalls>
