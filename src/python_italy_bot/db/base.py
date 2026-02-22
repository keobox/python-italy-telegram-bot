"""Abstract repository interface for persistence."""

from abc import ABC, abstractmethod


class Repository(ABC):
    """Abstract interface for data persistence (sync)."""

    @abstractmethod
    def add_pending_verification(self, user_id: int, chat_id: int) -> None:
        """Record that user joined chat and needs to complete captcha."""
        ...

    @abstractmethod
    def get_pending_chats(self, user_id: int) -> list[int]:
        """Return chat IDs where user is pending verification."""
        ...

    @abstractmethod
    def remove_pending(self, user_id: int, chat_id: int) -> bool:
        """Remove pending verification. Returns True if existed."""
        ...

    @abstractmethod
    def is_user_verified(self, user_id: int, chat_id: int) -> bool:
        """Check if user has completed captcha for the given chat."""
        ...

    @abstractmethod
    def mark_user_verified(self, user_id: int, chat_id: int) -> None:
        """Mark user as verified for the given chat."""
        ...

    @abstractmethod
    def get_banned_users(self, chat_id: int) -> list[int]:
        """Return user IDs banned in the given chat."""
        ...

    @abstractmethod
    def add_ban(
        self,
        user_id: int,
        chat_id: int,
        admin_id: int,
        reason: str | None = None,
    ) -> None:
        """Record a ban."""
        ...

    @abstractmethod
    def remove_ban(self, user_id: int, chat_id: int) -> bool:
        """Remove a ban. Returns True if ban existed."""
        ...

    @abstractmethod
    def get_muted_users(self, chat_id: int) -> list[int]:
        """Return user IDs currently muted in the given chat."""
        ...

    @abstractmethod
    def add_mute(
        self,
        user_id: int,
        chat_id: int,
        admin_id: int,
        reason: str | None = None,
        until: int | None = None,
    ) -> None:
        """Record a mute. until is Unix timestamp or None for indefinite."""
        ...

    @abstractmethod
    def remove_mute(self, user_id: int, chat_id: int) -> bool:
        """Remove a mute. Returns True if mute existed."""
        ...

    @abstractmethod
    def add_report(
        self,
        reporter_id: int,
        reported_user_id: int,
        chat_id: int,
        message_id: int | None = None,
        reason: str | None = None,
    ) -> None:
        """Record a report."""
        ...

    @abstractmethod
    def get_welcome_message(self, chat_id: int) -> str | None:
        """Get custom welcome message for a chat."""
        ...

    @abstractmethod
    def set_welcome_message(self, chat_id: int, message: str | None) -> None:
        """Set custom welcome message for a chat. Pass None to remove."""
        ...

    @abstractmethod
    def is_globally_verified(self, user_id: int) -> bool:
        """Check if user is globally verified across all chats."""
        ...

    @abstractmethod
    def mark_globally_verified(self, user_id: int) -> None:
        """Mark user as globally verified."""
        ...


class AsyncRepository(ABC):
    """Abstract interface for data persistence (async)."""

    @abstractmethod
    async def add_pending_verification(self, user_id: int, chat_id: int) -> None:
        """Record that user joined chat and needs to complete captcha."""
        ...

    @abstractmethod
    async def get_pending_chats(self, user_id: int) -> list[int]:
        """Return chat IDs where user is pending verification."""
        ...

    @abstractmethod
    async def remove_pending(self, user_id: int, chat_id: int) -> bool:
        """Remove pending verification. Returns True if existed."""
        ...

    @abstractmethod
    async def is_user_verified(self, user_id: int, chat_id: int) -> bool:
        """Check if user has completed captcha for the given chat."""
        ...

    @abstractmethod
    async def mark_user_verified(self, user_id: int, chat_id: int) -> None:
        """Mark user as verified for the given chat."""
        ...

    @abstractmethod
    async def get_banned_users(self, chat_id: int) -> list[int]:
        """Return user IDs banned in the given chat."""
        ...

    @abstractmethod
    async def add_ban(
        self,
        user_id: int,
        chat_id: int,
        admin_id: int,
        reason: str | None = None,
    ) -> None:
        """Record a ban."""
        ...

    @abstractmethod
    async def remove_ban(self, user_id: int, chat_id: int) -> bool:
        """Remove a ban. Returns True if ban existed."""
        ...

    @abstractmethod
    async def get_muted_users(self, chat_id: int) -> list[int]:
        """Return user IDs currently muted in the given chat."""
        ...

    @abstractmethod
    async def add_mute(
        self,
        user_id: int,
        chat_id: int,
        admin_id: int,
        reason: str | None = None,
        until: int | None = None,
    ) -> None:
        """Record a mute. until is Unix timestamp or None for indefinite."""
        ...

    @abstractmethod
    async def remove_mute(self, user_id: int, chat_id: int) -> bool:
        """Remove a mute. Returns True if mute existed."""
        ...

    @abstractmethod
    async def add_report(
        self,
        reporter_id: int,
        reported_user_id: int,
        chat_id: int,
        message_id: int | None = None,
        reason: str | None = None,
    ) -> None:
        """Record a report."""
        ...

    @abstractmethod
    async def get_welcome_message(self, chat_id: int) -> str | None:
        """Get custom welcome message for a chat."""
        ...

    @abstractmethod
    async def set_welcome_message(self, chat_id: int, message: str | None) -> None:
        """Set custom welcome message for a chat. Pass None to remove."""
        ...

    @abstractmethod
    async def is_globally_verified(self, user_id: int) -> bool:
        """Check if user is globally verified across all chats."""
        ...

    @abstractmethod
    async def mark_globally_verified(self, user_id: int) -> None:
        """Mark user as globally verified."""
        ...

    async def close(self) -> None:
        """Close any resources (override if needed)."""
        pass
