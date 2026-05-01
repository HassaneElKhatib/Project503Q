"""Async SQLAlchemy session factory.

Every service that talks to Postgres builds its engine via build_engine().
We use the asyncpg driver under SQLAlchemy's async API.

Pool sizing matters: each pod will keep `pool_size` connections open.
Postgres max_connections is finite, so don't set this too high per pod.
For dev (small RDS) keep pool_size around 5; for prod tune from real load.
"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from libs.logger import get_logger

logger = get_logger(__name__)


def build_engine(
    database_url: str,
    *,
    pool_size: int = 5,
    max_overflow: int = 5,
    pool_timeout: int = 10,
    echo: bool = False,
) -> AsyncEngine:
    """Create an async engine.

    database_url should be the asyncpg form, e.g.
        postgresql+asyncpg://user:pass@host:5432/db
    Plain "postgresql://" URLs are rewritten automatically.

    SQLite (used in tests) uses a StaticPool which doesn't accept the
    standard pool kwargs - we omit them in that case.
    """
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    is_sqlite = database_url.startswith("sqlite")
    kwargs: dict = {"echo": echo, "future": True}
    if not is_sqlite:
        kwargs.update(
            {
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "pool_timeout": pool_timeout,
                "pool_pre_ping": True,
            }
        )

    engine = create_async_engine(database_url, **kwargs)
    logger.info(
        "db engine built",
        extra={"sqlite": is_sqlite, "pool_size": pool_size if not is_sqlite else None},
    )
    return engine


def build_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,  # objects stay usable after commit
        autoflush=False,
    )


@asynccontextmanager
async def session_scope(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Async context manager that commits on success and rolls back on error."""
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def healthcheck(sessionmaker: async_sessionmaker[AsyncSession]) -> bool:
    """Used by /health/ready. Runs SELECT 1."""
    from sqlalchemy import text

    try:
        async with sessionmaker() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as exc:
        logger.warning("db healthcheck failed", extra={"error": str(exc)})
        return False
