# Database helpers: connection pool, LangGraph async checkpointer,
# and SQL migration runner.

from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncGenerator

import psycopg_pool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


def _db_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set.")
    return url


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"

# Module-level pool — initialised once on startup via lifespan.
_pool: psycopg_pool.AsyncConnectionPool | None = None

# Module-level checkpointer — initialised once on startup via lifespan.
_checkpointer: AsyncPostgresSaver | None = None


async def init_pool() -> None:
    """Create the async connection pool. Call once at app startup."""
    global _pool
    _pool = psycopg_pool.AsyncConnectionPool(
        conninfo=_db_url(),
        min_size=1,
        max_size=10,
        open=False,
    )
    await _pool.open()


async def init_checkpointer() -> AsyncPostgresSaver:
    """Create the AsyncPostgresSaver backed by the module pool. Call once at startup."""
    global _checkpointer
    _checkpointer = AsyncPostgresSaver(get_pool())
    return _checkpointer


async def close_pool() -> None:
    """Drain and close the pool. Call at app shutdown."""
    global _pool, _checkpointer
    if _pool:
        await _pool.close()
        _pool = None
        _checkpointer = None


def get_pool() -> psycopg_pool.AsyncConnectionPool:
    if _pool is None:
        raise RuntimeError("DB pool not initialised. Call init_pool() first.")
    return _pool


def get_checkpointer() -> AsyncPostgresSaver:
    if _checkpointer is None:
        raise RuntimeError("Checkpointer not initialised. Call init_checkpointer() first.")
    return _checkpointer


async def open_checkpointer() -> AsyncGenerator[AsyncPostgresSaver, None]:
    """Async-context wrapper around get_checkpointer() for callers that want
    a scoped handle. The underlying saver is shared (module-level)."""
    yield get_checkpointer()


async def setup_checkpointer_tables() -> None:
    """Create LangGraph checkpointer tables if they don't exist."""
    await get_checkpointer().setup()


async def run_migration(sql: str) -> None:
    """Execute a raw SQL migration string."""
    pool = get_pool()
    async with pool.connection() as conn:
        await conn.execute(sql)
        await conn.commit()


async def run_migrations() -> None:
    """Apply SQL files from migrations/ in lexical order. Idempotent —
    files use CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS."""
    pool = get_pool()
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    async with pool.connection() as conn:
        for path in files:
            await conn.execute(path.read_text())
        await conn.commit()
