-- PostgreSQL schema for Python Italy Telegram Bot
-- Run against your DATABASE_URL before using PostgresRepository

CREATE TABLE IF NOT EXISTS pending_verifications (
    user_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    PRIMARY KEY (user_id, chat_id)
);

CREATE TABLE IF NOT EXISTS verified_users (
    user_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    PRIMARY KEY (user_id, chat_id)
);

CREATE TABLE IF NOT EXISTS bans (
    user_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    admin_id BIGINT NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, chat_id)
);

CREATE TABLE IF NOT EXISTS mutes (
    user_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    admin_id BIGINT NOT NULL,
    reason TEXT,
    until_ts TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, chat_id)
);

CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    reporter_id BIGINT NOT NULL,
    reported_user_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    message_id BIGINT,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS group_settings (
    chat_id BIGINT PRIMARY KEY,
    welcome_message TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS globally_verified_users (
    user_id BIGINT PRIMARY KEY,
    verified_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bot_chats (
    chat_id BIGINT PRIMARY KEY,
    added_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS global_bans (
    user_id BIGINT PRIMARY KEY,
    admin_id BIGINT NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS known_users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_known_users_username
    ON known_users (LOWER(username))
    WHERE username IS NOT NULL;

CREATE TABLE IF NOT EXISTS welcomed_users (
    user_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    welcomed_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, chat_id)
);

-- Add welcome_delay_minutes column to group_settings (idempotent).
ALTER TABLE group_settings
    ADD COLUMN IF NOT EXISTS welcome_delay_minutes INTEGER;
