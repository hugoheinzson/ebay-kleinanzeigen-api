"""Database session and engine management."""

from __future__ import annotations

import asyncio
import os
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .models import Base

_ENGINE: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def _database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./kleinanzeigen.db")


def _engine_echo() -> bool:
    return os.getenv("DATABASE_ECHO", "0") in {"1", "true", "True"}


def get_engine() -> AsyncEngine:
    global _ENGINE
    if _ENGINE is None:
        database_url = _database_url()
        logger.info("Initializing database engine", url=database_url)
        _ENGINE = create_async_engine(database_url, echo=_engine_echo(), future=True)
    return _ENGINE


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the lazily initialised session factory."""

    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _async_session_factory


async def init_db() -> None:
    """Create database schema if it does not yet exist."""

    engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose the database engine and close open connections."""

    global _ENGINE, _async_session_factory
    engine = _ENGINE
    _async_session_factory = None
    if engine is not None:
        await engine.dispose()
        _ENGINE = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession for FastAPI dependencies."""

    factory = get_session_factory()
    async with factory() as session:
        yield session


async def reset_database_state() -> None:
    """Utility for tests to reset engine/session."""

    await close_db()
    # Ensure engine/session re-initialized lazily on next use
    # If running within asyncio loop ensure context switch
    await asyncio.sleep(0)
