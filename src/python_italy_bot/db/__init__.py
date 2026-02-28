"""Database abstraction layer."""

from .base import AsyncRepository, Repository
from .in_memory import InMemoryRepository
from .models import Ban, Chat, Mute, Report
from .postgres import PostgresRepository

__all__ = [
    "Repository",
    "AsyncRepository",
    "InMemoryRepository",
    "PostgresRepository",
    "Ban",
    "Chat",
    "Mute",
    "Report",
    "create_repository",
]


async def create_repository(database_url: str | None) -> AsyncRepository:
    """Create a repository based on the database URL.

    Returns PostgresRepository if database_url is a PostgreSQL URL,
    otherwise returns InMemoryRepository.
    """
    if database_url and database_url.startswith("postgresql"):
        from psycopg_pool import AsyncConnectionPool

        pool = AsyncConnectionPool(
            database_url,
            open=False,
            check=AsyncConnectionPool.check_connection,
            max_lifetime=300,
        )
        await pool.open()
        return PostgresRepository(pool)
    return InMemoryRepository()
