"""Captcha verification logic (file + secret command flow)."""

from pathlib import Path

from telegram import ChatPermissions

from ..db.base import AsyncRepository


class CaptchaService:
    """Handles welcome captcha: restrict new members until they send secret command in DM."""

    def __init__(
        self, repository: AsyncRepository, secret_command: str, file_path: str
    ) -> None:
        self._repo = repository
        self._secret_command = secret_command.strip().lower()
        self._file_path = Path(file_path)

    def _matches_secret(self, text: str) -> bool:
        return text.strip().lower() == self._secret_command

    def get_welcome_message(self) -> str:
        """Return the welcome message with captcha instructions."""
        return (
            "Benvenuto nel gruppo Python Italia! 🐍\n\n"
            "Per poter partecipare alle discussioni, leggere il file delle regole "
            "e inviare il comando segreto che troverai al bot in chat privata.\n\n"
            "Per aprire una chat con il bot, clicca sul suo nome e seleziona 'Avvia'."
        )

    def get_captcha_file_content(self) -> str | None:
        """Return the captcha file content if it exists. Path is relative to cwd."""
        path = Path(self._file_path)
        if path.is_absolute():
            full = path
        else:
            full = Path.cwd() / path
        if full.exists():
            return full.read_text(encoding="utf-8")
        return None

    def get_restricted_permissions(self) -> ChatPermissions:
        """Permissions for unverified users (can read but not send)."""
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

    def get_full_permissions(self) -> ChatPermissions:
        """Full permissions for verified users."""
        return ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=False,
        )

    def is_secret_command(self, text: str) -> bool:
        """Check if the message matches the secret command."""
        return self._matches_secret(text)

    async def get_pending_chats(self, user_id: int) -> list[int]:
        """Get chats where user is pending verification."""
        return await self._repo.get_pending_chats(user_id)

    async def verify_user(self, user_id: int, chat_id: int) -> None:
        """Mark user as verified and remove from pending."""
        await self._repo.mark_user_verified(user_id, chat_id)
        await self._repo.remove_pending(user_id, chat_id)

    async def add_pending(self, user_id: int, chat_id: int) -> None:
        """Record that user joined and needs verification."""
        await self._repo.add_pending_verification(user_id, chat_id)

    async def is_verified(self, user_id: int, chat_id: int) -> bool:
        """Check if user is verified for the chat."""
        return await self._repo.is_user_verified(user_id, chat_id)
