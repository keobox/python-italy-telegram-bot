"""Spam detection logic with pluggable rules."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from telegram import Message


@dataclass
class SpamResult:
    """Result of spam check."""

    is_spam: bool
    reason: str | None = None


class SpamDetector:
    """Detects spam using configurable rules."""

    def __init__(
        self,
        max_messages_per_minute: int = 5,
        duplicate_threshold_seconds: int = 60,
    ) -> None:
        self._max_messages_per_minute = max_messages_per_minute
        self._duplicate_threshold_seconds = duplicate_threshold_seconds
        self._message_history: dict[int, list[datetime]] = defaultdict(list)
        self._last_message_text: dict[int, tuple[str, datetime]] = {}

    def _clean_old_entries(self, user_id: int) -> None:
        """Remove old entries from message history."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=2)
        self._message_history[user_id] = [
            ts for ts in self._message_history[user_id] if ts > cutoff
        ]

    def _clean_duplicate_cache(self, user_id: int) -> None:
        """Remove stale duplicate cache entries."""
        last_text, last_ts = self._last_message_text.get(
            user_id, ("", datetime.min.replace(tzinfo=timezone.utc))
        )
        cutoff = datetime.now(timezone.utc) - timedelta(
            seconds=self._duplicate_threshold_seconds
        )
        if last_ts < cutoff:
            self._last_message_text.pop(user_id, None)

    def check(self, message: Message) -> SpamResult:
        """Check if a message is spam."""
        user = message.from_user
        if user is None:
            return SpamResult(is_spam=False)

        user_id = user.id
        now = datetime.now(timezone.utc)

        # Rate limiting
        self._clean_old_entries(user_id)
        self._message_history[user_id].append(now)
        recent = [
            ts
            for ts in self._message_history[user_id]
            if ts > now - timedelta(minutes=1)
        ]
        if len(recent) > self._max_messages_per_minute:
            return SpamResult(
                is_spam=True,
                reason="Troppi messaggi in poco tempo (rate limit)",
            )

        # Duplicate messages
        text = message.text or message.caption or ""
        self._clean_duplicate_cache(user_id)
        last_text, last_ts = self._last_message_text.get(
            user_id, ("", datetime.min.replace(tzinfo=timezone.utc))
        )
        if text and last_text == text:
            if (now - last_ts).total_seconds() < self._duplicate_threshold_seconds:
                return SpamResult(
                    is_spam=True,
                    reason="Messaggio duplicato",
                )
        if text:
            self._last_message_text[user_id] = (text, now)

        return SpamResult(is_spam=False)
