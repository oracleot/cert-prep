# Database helpers: connection pool, LangGraph async checkpointer,
# and SQL migration runner.

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, AsyncGenerator

import psycopg_pool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

logger = logging.getLogger(__name__)


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
_checkpointer: Any | None = None


async def init_pool() -> None:
    """Create the async connection pool when DATABASE_URL is available."""
    global _pool
    if not os.environ.get("DATABASE_URL"):
        logger.warning("DATABASE_URL is not set. Falling back to in-memory sessions.")
        _pool = None
        return

    if _pool is not None:
        return

    _pool = psycopg_pool.AsyncConnectionPool(
        conninfo=_db_url(),
        min_size=1,
        max_size=10,
        open=False,
    )
    try:
        await _pool.open()
    except Exception:
        logger.exception("Failed to open Postgres pool. Falling back to in-memory sessions.")
        _pool = None


async def init_checkpointer() -> Any:
    """Create the configured checkpointer for the current persistence mode."""
    global _checkpointer
    if _pool is None:
        _checkpointer = InMemorySaver()
        return _checkpointer

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


def get_checkpointer() -> Any:
    if _checkpointer is None:
        raise RuntimeError("Checkpointer not initialised. Call init_checkpointer() first.")
    return _checkpointer


def has_pool() -> bool:
    return _pool is not None


async def open_checkpointer() -> AsyncGenerator[Any, None]:
    """Async-context wrapper around get_checkpointer() for callers that want
    a scoped handle. The underlying saver is shared (module-level)."""
    yield get_checkpointer()


async def setup_checkpointer_tables() -> None:
    """Create LangGraph checkpointer tables if they don't exist.

    Workaround for langgraph-checkpoint-postgres==2.0.3: its setup() runs
    the initial version-probe SELECT inside the same transaction as the
    migration loop. On a fresh DB the SELECT raises UndefinedTable, which
    puts the transaction into an aborted state — so the subsequent CREATE
    TABLE statements fail with InFailedSqlTransaction.

    To avoid relying on the broken setup(), we pre-create the four
    checkpointer tables ourselves in autocommit mode, register them at
    the latest version in checkpoint_migrations, and then let setup() run
    a no-op pass.
    """
    from langgraph.checkpoint.postgres.base import MIGRATIONS

    if _pool is None:
        return

    pool = get_pool()
    last_version = len(MIGRATIONS) - 1

    async with pool.connection() as conn:
        was_autocommit = conn.autocommit
        await conn.set_autocommit(True)
        try:
            for sql in MIGRATIONS:
                await conn.execute(sql)
            await conn.execute(
                "INSERT INTO checkpoint_migrations (v) VALUES (%s) "
                "ON CONFLICT (v) DO NOTHING",
                (last_version,),
            )
        finally:
            await conn.set_autocommit(was_autocommit)


async def run_migration(sql: str) -> None:
    """Execute a raw SQL migration string."""
    if _pool is None:
        return

    pool = get_pool()
    async with pool.connection() as conn:
        await conn.execute(sql)
        await conn.commit()


async def run_migrations() -> None:
    """Apply SQL files from migrations/ in lexical order. Idempotent —
    files use CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS."""
    if _pool is None:
        return

    pool = get_pool()
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    async with pool.connection() as conn:
        for path in files:
            await conn.execute(path.read_text())
        await conn.commit()
