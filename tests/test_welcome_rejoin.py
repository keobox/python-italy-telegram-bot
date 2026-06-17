"""Tests for the rejoin fix: leaving a chat clears welcome/pending state.

A user who is restricted by the captcha flow and then leaves must have the
'welcomed' and 'pending' flags cleared, so that a genuine rejoin re-triggers
the captcha instead of being silently re-muted forever.
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from telegram.constants import ChatMemberStatus

from python_italy_bot.db.in_memory import InMemoryRepository
from python_italy_bot.handlers.welcome import _handle_new_member
from python_italy_bot.services.captcha import CaptchaService
from python_italy_bot.services.moderation import ModerationService


# -- Repository: remove_welcomed --


def test_remove_welcomed_clears_flag() -> None:
    """remove_welcomed clears a previously set welcomed flag."""
    repo = InMemoryRepository()
    asyncio.run(repo.mark_welcomed(999, -100))
    assert asyncio.run(repo.has_been_welcomed(999, -100)) is True
    asyncio.run(repo.remove_welcomed(999, -100))
    assert asyncio.run(repo.has_been_welcomed(999, -100)) is False


def test_remove_welcomed_missing_is_noop() -> None:
    """remove_welcomed on a missing entry does not raise."""
    repo = InMemoryRepository()
    asyncio.run(repo.remove_welcomed(999, -100))
    assert asyncio.run(repo.has_been_welcomed(999, -100)) is False


# -- Handler: departure clears welcome/pending state --


def _make_departure_update(status: ChatMemberStatus):
    user = SimpleNamespace(id=999, is_bot=False, username="u", full_name="U")
    new_member = SimpleNamespace(status=status, user=user)
    old_member = SimpleNamespace(status=ChatMemberStatus.RESTRICTED)
    chat_member = SimpleNamespace(
        new_chat_member=new_member, old_chat_member=old_member
    )
    chat = SimpleNamespace(id=-100, title="PythonMilano", type="supergroup")
    return SimpleNamespace(chat_member=chat_member, effective_chat=chat)


def _make_context(repo: InMemoryRepository):
    captcha = CaptchaService(repo, "python-italy", "assets/regolamento.md")
    moderation = ModerationService(repo)
    return SimpleNamespace(
        bot=AsyncMock(),
        bot_data={
            "captcha_service": captcha,
            "moderation_service": moderation,
            "repository": repo,
        },
    )


def test_member_leaving_clears_welcome_and_pending() -> None:
    """When a restricted member leaves, welcomed + pending state is cleared."""
    repo = InMemoryRepository()
    asyncio.run(repo.mark_welcomed(999, -100))
    asyncio.run(repo.add_pending_verification(999, -100))

    update = _make_departure_update(ChatMemberStatus.LEFT)
    context = _make_context(repo)

    asyncio.run(_handle_new_member(update, context))

    assert asyncio.run(repo.has_been_welcomed(999, -100)) is False
    assert asyncio.run(repo.get_pending_chats(999)) == []


def test_member_kicked_clears_welcome_and_pending() -> None:
    """A kicked/banned member also has welcomed + pending state cleared."""
    repo = InMemoryRepository()
    asyncio.run(repo.mark_welcomed(999, -100))
    asyncio.run(repo.add_pending_verification(999, -100))

    update = _make_departure_update(ChatMemberStatus.BANNED)
    context = _make_context(repo)

    asyncio.run(_handle_new_member(update, context))

    assert asyncio.run(repo.has_been_welcomed(999, -100)) is False
    assert asyncio.run(repo.get_pending_chats(999)) == []


def test_leaving_does_not_clear_global_verification() -> None:
    """Leaving must NOT clear global verification (verified users stay verified)."""
    repo = InMemoryRepository()
    asyncio.run(repo.mark_globally_verified(999))

    update = _make_departure_update(ChatMemberStatus.LEFT)
    context = _make_context(repo)

    asyncio.run(_handle_new_member(update, context))

    assert asyncio.run(repo.is_globally_verified(999)) is True
