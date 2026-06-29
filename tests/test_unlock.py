"""Tests for the /unlock command.

/unlock is the admin tool to free a user who is stuck in the captcha
('pending verification') state — distinct from /unmute, which reverses a
moderation /mute. It globally verifies the user, clears pending state, and
restores send permissions in their pending chats.
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from telegram.constants import ChatMemberStatus

from python_italy_bot import strings
from python_italy_bot.db.in_memory import InMemoryRepository
from python_italy_bot.handlers.moderation import _handle_unlock
from python_italy_bot.services.captcha import CaptchaService
from python_italy_bot.services.moderation import ModerationService


def _make_setup(admin_status: ChatMemberStatus = ChatMemberStatus.ADMINISTRATOR):
    repo = InMemoryRepository()
    captcha = CaptchaService(repo, "python-italy", "assets/regolamento.md")
    moderation = ModerationService(repo)

    bot = AsyncMock()
    bot.get_chat_member = AsyncMock(return_value=SimpleNamespace(status=admin_status))
    bot.restrict_chat_member = AsyncMock()

    admin = SimpleNamespace(id=1)
    target = SimpleNamespace(id=999)
    reply = SimpleNamespace(from_user=target)
    message = SimpleNamespace(
        from_user=admin,
        text="/unlock",
        reply_to_message=reply,
        reply_text=AsyncMock(),
    )
    chat = SimpleNamespace(id=-100, type="supergroup", title="PythonMilano")
    update = SimpleNamespace(message=message, effective_chat=chat)
    context = SimpleNamespace(
        bot=bot,
        bot_data={"moderation_service": moderation, "captcha_service": captcha},
    )
    return repo, update, context, bot, message


def test_unlock_verifies_globally_and_clears_pending() -> None:
    """/unlock marks the user globally verified and clears pending state."""
    repo, update, context, bot, message = _make_setup()
    asyncio.run(repo.add_pending_verification(999, -100))

    asyncio.run(_handle_unlock(update, context))

    assert asyncio.run(repo.is_globally_verified(999)) is True
    assert asyncio.run(repo.get_pending_chats(999)) == []
    message.reply_text.assert_awaited_with(strings.UNLOCK_SUCCESS)


def test_unlock_restores_permissions_in_chat() -> None:
    """/unlock restores send permissions via restrict_chat_member."""
    repo, update, context, bot, message = _make_setup()
    asyncio.run(repo.add_pending_verification(999, -100))

    asyncio.run(_handle_unlock(update, context))

    bot.restrict_chat_member.assert_awaited()
    # full permissions must allow sending messages
    kwargs = bot.restrict_chat_member.await_args.kwargs
    perms = kwargs["permissions"]
    assert perms.can_send_messages is True
    # defensive: must NOT elevate pin / change-info above group default
    assert perms.can_change_info is False
    assert perms.can_pin_messages is False


def test_unlock_rejects_non_admin() -> None:
    """A non-admin cannot use /unlock; no state changes occur."""
    repo, update, context, bot, message = _make_setup(
        admin_status=ChatMemberStatus.MEMBER
    )
    asyncio.run(repo.add_pending_verification(999, -100))

    asyncio.run(_handle_unlock(update, context))

    assert asyncio.run(repo.is_globally_verified(999)) is False
    assert asyncio.run(repo.get_pending_chats(999)) == [-100]
    bot.restrict_chat_member.assert_not_awaited()
    message.reply_text.assert_awaited_with(strings.ONLY_ADMINS)


def test_unlock_ignored_in_private_chat() -> None:
    """/unlock does nothing in a private chat."""
    repo, update, context, bot, message = _make_setup()
    update.effective_chat = SimpleNamespace(id=1, type="private", title=None)
    asyncio.run(repo.add_pending_verification(999, -100))

    asyncio.run(_handle_unlock(update, context))

    assert asyncio.run(repo.is_globally_verified(999)) is False
    bot.restrict_chat_member.assert_not_awaited()
