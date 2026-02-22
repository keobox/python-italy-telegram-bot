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

## Running the bot

Start the bot:

```bash
uv run python-italy-bot
```

The bot starts polling for updates. You should see:

```
INFO - Starting bot...
INFO - Application started
```

Stop with `Ctrl+C`.

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token from [@BotFather](https://t.me/BotFather) |
| `DATABASE_URL` | No | PostgreSQL URL (Neon or other). When set, uses PostgresRepository; otherwise in-memory. |
| `CAPTCHA_SECRET_COMMAND` | No | Secret command for captcha (default: `python-italy`) |
| `CAPTCHA_FILE_PATH` | No | Path to rules file (default: `assets/regolamento.md`) |
| `MAIN_GROUP_ID` | No | Main group ID for multi-group logic |
| `LOCAL_GROUP_IDS` | No | Comma-separated sub-group IDs |

## Commands

| Command | Who | Description |
|---------|-----|-------------|
| `/ban` | Admin | Ban a user. |
| `/unban` | Admin | Unban a user. |
| `/mute` | Admin | Mute a user (optionally for N minutes). |
| `/unmute` | Admin | Unmute a user. |
| `/report` | Anyone | Report a message. |

### Usage

- **Ban**: `/ban @username`, `/ban user_id [reason]`, or reply to a message with `/ban [reason]`
- **Unban**: `/unban @username`, `/unban user_id`, or reply to user's message
- **Mute**: `/mute @username [minutes] [reason]`, or reply to message. Omit minutes for indefinite mute.
- **Unmute**: `/unmute @username`, `/unmute user_id`, or reply to user's message
- **Report**: Reply to the offending message with `/report [reason]`

### Captcha (secret command)

New members must send the secret command in DM to the bot. Default: `python-italy` (configurable via `CAPTCHA_SECRET_COMMAND`). Send it as plain text in a private chat with the bot.

## Testing the bot

1. **Add the bot to a group**: Make the bot an admin so it can restrict members and ban/mute users.

2. **Test captcha**:
   - Join the group with a test account (not admin).
   - You should be restricted (read-only).
   - Open a private chat with the bot and send the secret command (e.g. `python-italy`).
   - You should be unrestricted in the group.

3. **Test moderation** (as admin):
   - `/ban @username` or reply to a message with `/ban [reason]`
   - `/unban @username` to unban
   - `/mute @username 60` to mute for 60 minutes
   - `/unmute @username` to unmute

4. **Test report** (as any member):
   - Reply to a message with `/report spam` (or any reason).

## Architecture

```
src/python_italy_bot/
├── main.py           # Entry point, Application setup
├── config.py         # Settings from env
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
