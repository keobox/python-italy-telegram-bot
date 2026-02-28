"""Moderation logic: bans, mutes, reports."""

from telegram import ChatPermissions

from ..db.base import AsyncRepository
from ..db.models import KnownUser


class ModerationService:
    """Handles ban, mute, and report operations."""

    def __init__(self, repository: AsyncRepository) -> None:
        self._repo = repository

    def get_mute_permissions(self) -> ChatPermissions:
        """Permissions for muted users (read-only)."""
        return ChatPermissions(
            can_send_messages=False,
            can_send_audios=False,
            can_send_documents=False,
            can_send_photos=False,
            can_send_videos=False,
            can_send_video_notes=False,
            can_send_voice_notes=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
        )

    async def is_banned(self, user_id: int, chat_id: int) -> bool:
        """Check if user is banned in chat."""
        banned_users = await self._repo.get_banned_users(chat_id)
        return user_id in banned_users

    async def is_muted(self, user_id: int, chat_id: int) -> bool:
        """Check if user is muted in chat."""
        muted_users = await self._repo.get_muted_users(chat_id)
        return user_id in muted_users

    async def add_global_ban(
        self,
        user_id: int,
        admin_id: int,
        reason: str | None = None,
    ) -> list[int]:
        """Record a global ban. Returns list of chat IDs to ban in."""
        await self._repo.add_global_ban(
            user_id=user_id, admin_id=admin_id, reason=reason
        )
        return await self._repo.get_all_chats()

    async def remove_global_ban(self, user_id: int) -> list[int]:
        """Remove a global ban. Returns list of chat IDs to unban in."""
        await self._repo.remove_global_ban(user_id)
        return await self._repo.get_all_chats()

    async def is_globally_banned(self, user_id: int) -> bool:
        """Check if user is globally banned."""
        return await self._repo.is_globally_banned(user_id)

    async def register_chat(self, chat_id: int) -> None:
        """Register a chat where the bot is active."""
        await self._repo.register_chat(chat_id)

    async def get_all_chats(self) -> list[int]:
        """Get all tracked chat IDs."""
        return await self._repo.get_all_chats()

    async def add_mute(
        self,
        user_id: int,
        chat_id: int,
        admin_id: int,
        reason: str | None = None,
        until: int | None = None,
    ) -> None:
        """Record a mute."""
        await self._repo.add_mute(
            user_id=user_id,
            chat_id=chat_id,
            admin_id=admin_id,
            reason=reason,
            until=until,
        )

    async def remove_mute(self, user_id: int, chat_id: int) -> bool:
        """Remove a mute record."""
        return await self._repo.remove_mute(user_id, chat_id)

    async def add_report(
        self,
        reporter_id: int,
        reported_user_id: int,
        chat_id: int,
        message_id: int | None = None,
        reason: str | None = None,
    ) -> None:
        """Record a report."""
        await self._repo.add_report(
            reporter_id=reporter_id,
            reported_user_id=reported_user_id,
            chat_id=chat_id,
            message_id=message_id,
            reason=reason,
        )

    # -- Known users (user tracking) --

    async def upsert_known_user(
        self,
        user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> None:
        """Insert or update a known user's info."""
        await self._repo.upsert_known_user(user_id, username, first_name, last_name)

    async def get_known_user_by_username(self, username: str) -> KnownUser | None:
        """Get a known user by username (case-insensitive)."""
        return await self._repo.get_known_user_by_username(username)
