# Python Italy Telegram Bot

Official Telegram bot for the main Italian Python group and local sub-groups in Italy.

## Features

- **Welcome captcha**: New members must read a rules file and send a secret command to the bot in private chat before they can post in the group
- **Spam detection**: Rate limiting and duplicate message detection with automatic deletion
- **Moderation**: Ban, mute, and report commands (admin-only for ban/mute)
- **Database abstraction**: In-memory storage by default; persistent database can be added later

## Requirements

- Python 3.14+
- [UV](https://docs.astral.sh/uv/) package manager

## Setup

1. Install UV if needed:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Copy the environment template and configure:
   ```bash
   cp .env.example .env
   # Edit .env and set TELEGRAM_BOT_TOKEN
   ```

4. If using PostgreSQL (`DATABASE_URL` set), create the schema:
   ```bash
   psql "$DATABASE_URL" -f schema.sql
   ```

5. Run the bot:
   ```bash
   uv run python-italy-bot
   # or: uv run python -m python_italy_bot.main
   ```

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from [@BotFather](https://t.me/BotFather) |
| `DATABASE_URL` | No | Database URL (placeholder for future use) |
| `CAPTCHA_SECRET_COMMAND` | No | Secret command for captcha (default: `python-italy`) |
| `CAPTCHA_FILE_PATH` | No | Path to rules file (default: `assets/regolamento.md`) |
| `MAIN_GROUP_ID` | No | Main group ID for multi-group logic |
| `LOCAL_GROUP_IDS` | No | Comma-separated sub-group IDs |

## Commands

- `/ban` – Ban a user (admin only). Usage: `/ban @username`, `/ban user_id [reason]`, or reply to message with `/ban [reason]`
- `/unban` – Unban a user (admin only)
- `/mute` – Mute a user (admin only). Usage: `/mute @username [minutes] [reason]`
- `/unmute` – Unmute a user (admin only)
- `/report` – Report a message. Reply to the message with `/report [reason]`

## Architecture

```
src/python_italy_bot/
├── main.py           # Entry point, Application setup
├── config.py         # Pydantic settings from env
├── handlers/         # Telegram update handlers
│   ├── welcome.py    # New member + captcha flow
│   ├── moderation.py # Ban, mute, report commands
│   └── spam.py       # Spam detection
├── services/         # Business logic
│   ├── captcha.py    # Captcha verification
│   ├── spam_detector.py
│   └── moderation.py
├── db/               # Persistence abstraction
│   ├── base.py       # Repository interface
│   ├── models.py     # Domain models
│   └── in_memory.py  # In-memory implementation
└── assets/           # Captcha/rules file
```

## Captcha Flow

1. User joins group → Bot restricts them (read-only)
2. Bot sends welcome message with instructions
3. User reads the rules file and finds the secret command
4. User sends the secret command to the bot in private chat
5. Bot verifies and removes restrictions in the group

## License

MIT
