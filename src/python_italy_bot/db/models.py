"""Domain models for persistence (no ORM)."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Ban:
    """A user ban in a chat."""

    user_id: int
    chat_id: int
    admin_id: int
    reason: str | None
    created_at: datetime


@dataclass
class Mute:
    """A user mute in a chat."""

    user_id: int
    chat_id: int
    admin_id: int
    reason: str | None
    until: datetime | None
    created_at: datetime


@dataclass
class Report:
    """A user report in a chat."""

    reporter_id: int
    reported_user_id: int
    chat_id: int
    message_id: int | None
    reason: str | None
    created_at: datetime
