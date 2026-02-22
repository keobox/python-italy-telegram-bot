"""In-memory implementation of the repository (no persistent DB)."""

from datetime import datetime, timezone

from .base import AsyncRepository
from .models import Ban, Mute, Report


class InMemoryRepository(AsyncRepository):
    """In-memory repository for development and testing."""

    def __init__(self) -> None:
        self._verified: set[tuple[int, int]] = set()
        self._pending: set[tuple[int, int]] = set()
        self._bans: list[Ban] = []
        self._mutes: list[Mute] = []
        self._reports: list[Report] = []

    async def add_pending_verification(self, user_id: int, chat_id: int) -> None:
        self._pending.add((user_id, chat_id))

    async def get_pending_chats(self, user_id: int) -> list[int]:
        return [c for u, c in self._pending if u == user_id]

    async def remove_pending(self, user_id: int, chat_id: int) -> bool:
        key = (user_id, chat_id)
        if key in self._pending:
            self._pending.discard(key)
            return True
        return False

    async def is_user_verified(self, user_id: int, chat_id: int) -> bool:
        return (user_id, chat_id) in self._verified

    async def mark_user_verified(self, user_id: int, chat_id: int) -> None:
        self._verified.add((user_id, chat_id))

    async def get_banned_users(self, chat_id: int) -> list[int]:
        return [b.user_id for b in self._bans if b.chat_id == chat_id]

    async def add_ban(
        self,
        user_id: int,
        chat_id: int,
        admin_id: int,
        reason: str | None = None,
    ) -> None:
        self._bans.append(
            Ban(
                user_id=user_id,
                chat_id=chat_id,
                admin_id=admin_id,
                reason=reason,
                created_at=datetime.now(timezone.utc),
            )
        )

    async def remove_ban(self, user_id: int, chat_id: int) -> bool:
        before = len(self._bans)
        self._bans = [
            b for b in self._bans if not (b.user_id == user_id and b.chat_id == chat_id)
        ]
        return len(self._bans) < before

    async def get_muted_users(self, chat_id: int) -> list[int]:
        now = datetime.now(timezone.utc)
        return [
            m.user_id
            for m in self._mutes
            if m.chat_id == chat_id and (m.until is None or m.until > now)
        ]

    async def add_mute(
        self,
        user_id: int,
        chat_id: int,
        admin_id: int,
        reason: str | None = None,
        until: int | None = None,
    ) -> None:
        until_dt = datetime.fromtimestamp(until, tz=timezone.utc) if until else None
        self._mutes.append(
            Mute(
                user_id=user_id,
                chat_id=chat_id,
                admin_id=admin_id,
                reason=reason,
                until=until_dt,
                created_at=datetime.now(timezone.utc),
            )
        )

    async def remove_mute(self, user_id: int, chat_id: int) -> bool:
        before = len(self._mutes)
        self._mutes = [
            m
            for m in self._mutes
            if not (m.user_id == user_id and m.chat_id == chat_id)
        ]
        return len(self._mutes) < before

    async def add_report(
        self,
        reporter_id: int,
        reported_user_id: int,
        chat_id: int,
        message_id: int | None = None,
        reason: str | None = None,
    ) -> None:
        self._reports.append(
            Report(
                reporter_id=reporter_id,
                reported_user_id=reported_user_id,
                chat_id=chat_id,
                message_id=message_id,
                reason=reason,
                created_at=datetime.now(timezone.utc),
            )
        )
