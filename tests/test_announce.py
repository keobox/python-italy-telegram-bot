"""Tests for InMemoryRepository chat methods and announce target parsing."""

import asyncio

from python_italy_bot.db.in_memory import InMemoryRepository
from python_italy_bot.handlers.announce import _parse_target_and_message
from python_italy_bot.services.moderation import ModerationService


# -- InMemoryRepository tests --


def test_register_chat_without_title() -> None:
    """Register a chat without title stores None."""
    repo = InMemoryRepository()
    asyncio.run(repo.register_chat(-100123))
    chats = asyncio.run(repo.get_all_chats())
    assert chats == [-100123]


def test_register_chat_with_title() -> None:
    """Register a chat with title stores both."""
    repo = InMemoryRepository()
    asyncio.run(repo.register_chat(-100123, "Python Italia"))
    chats = asyncio.run(repo.get_all_chats_with_titles())
    assert len(chats) == 1
    assert chats[0].chat_id == -100123
    assert chats[0].title == "Python Italia"


def test_register_chat_updates_title() -> None:
    """Re-registering a chat updates its title."""
    repo = InMemoryRepository()
    asyncio.run(repo.register_chat(-100123, "Old Name"))
    asyncio.run(repo.register_chat(-100123, "New Name"))
    chats = asyncio.run(repo.get_all_chats_with_titles())
    assert len(chats) == 1
    assert chats[0].title == "New Name"


def test_get_all_chats_returns_ids_only() -> None:
    """get_all_chats returns only chat IDs."""
    repo = InMemoryRepository()
    asyncio.run(repo.register_chat(-100001, "Group A"))
    asyncio.run(repo.register_chat(-100002, "Group B"))
    chats = asyncio.run(repo.get_all_chats())
    assert set(chats) == {-100001, -100002}


def test_get_all_chats_with_titles_returns_chat_objects() -> None:
    """get_all_chats_with_titles returns Chat dataclass instances."""
    repo = InMemoryRepository()
    asyncio.run(repo.register_chat(-100001, "Group A"))
    asyncio.run(repo.register_chat(-100002))
    chats = asyncio.run(repo.get_all_chats_with_titles())
    assert len(chats) == 2
    by_id = {c.chat_id: c for c in chats}
    assert by_id[-100001].title == "Group A"
    assert by_id[-100002].title is None


def test_find_chats_by_title_case_insensitive() -> None:
    """find_chats_by_title matches case-insensitively."""
    repo = InMemoryRepository()
    asyncio.run(repo.register_chat(-100001, "Python Italia"))
    asyncio.run(repo.register_chat(-100002, "Python Torino"))
    asyncio.run(repo.register_chat(-100003, "JavaScript Italia"))

    results = asyncio.run(repo.find_chats_by_title("python"))
    assert len(results) == 2
    ids = {c.chat_id for c in results}
    assert ids == {-100001, -100002}


def test_find_chats_by_title_partial_match() -> None:
    """find_chats_by_title matches partial strings."""
    repo = InMemoryRepository()
    asyncio.run(repo.register_chat(-100001, "Python Italia"))
    results = asyncio.run(repo.find_chats_by_title("Ital"))
    assert len(results) == 1
    assert results[0].chat_id == -100001


def test_find_chats_by_title_no_match() -> None:
    """find_chats_by_title returns empty list when no match."""
    repo = InMemoryRepository()
    asyncio.run(repo.register_chat(-100001, "Python Italia"))
    results = asyncio.run(repo.find_chats_by_title("Rust"))
    assert results == []


def test_find_chats_by_title_skips_none_titles() -> None:
    """find_chats_by_title skips chats without a title."""
    repo = InMemoryRepository()
    asyncio.run(repo.register_chat(-100001))
    results = asyncio.run(repo.find_chats_by_title("anything"))
    assert results == []


# -- ModerationService delegation tests --


def test_moderation_service_register_chat_with_title() -> None:
    """ModerationService.register_chat forwards title to repository."""
    repo = InMemoryRepository()
    service = ModerationService(repo)
    asyncio.run(service.register_chat(-100001, "Test Group"))
    chats = asyncio.run(service.get_all_chats_with_titles())
    assert len(chats) == 1
    assert chats[0].title == "Test Group"


def test_moderation_service_find_chats_by_title() -> None:
    """ModerationService.find_chats_by_title delegates to repository."""
    repo = InMemoryRepository()
    service = ModerationService(repo)
    asyncio.run(service.register_chat(-100001, "Python Italia"))
    asyncio.run(service.register_chat(-100002, "Python Torino"))
    results = asyncio.run(service.find_chats_by_title("Torino"))
    assert len(results) == 1
    assert results[0].chat_id == -100002


# -- Target parsing tests --


def test_parse_target_and_message_with_pipe() -> None:
    """Pipe separator splits target from message."""
    target, message = _parse_target_and_message("Python Italia | Hello everyone!")
    assert target == "Python Italia"
    assert message == "Hello everyone!"


def test_parse_target_and_message_without_pipe() -> None:
    """No pipe means no target, full text is message."""
    target, message = _parse_target_and_message("Hello everyone!")
    assert target is None
    assert message == "Hello everyone!"


def test_parse_target_and_message_numeric_id() -> None:
    """Numeric target with pipe."""
    target, message = _parse_target_and_message("-100123 | Announcement")
    assert target == "-100123"
    assert message == "Announcement"


def test_parse_target_and_message_username() -> None:
    """Username target with pipe."""
    target, message = _parse_target_and_message("@pythonita | News update")
    assert target == "@pythonita"
    assert message == "News update"


def test_parse_target_and_message_pipe_in_message() -> None:
    """Only the first pipe is used as delimiter."""
    target, message = _parse_target_and_message("group | msg with | pipe")
    assert target == "group"
    assert message == "msg with | pipe"


def test_parse_target_and_message_empty_target() -> None:
    """Empty target before pipe falls back to no-target mode."""
    target, message = _parse_target_and_message(" | Hello")
    assert target is None
    assert message == " | Hello"


def test_parse_target_and_message_empty_message() -> None:
    """Empty message after pipe falls back to no-target mode."""
    target, message = _parse_target_and_message("group | ")
    assert target is None
    assert message == "group | "
