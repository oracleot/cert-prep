# Application table CRUD: sessions and exchanges.
# LangGraph checkpointer tables are managed separately by
# AsyncPostgresSaver.setup() in db.py.

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from db import get_pool


async def create_session(user_id: str, exam_id: str, domain: str) -> str:
    """Insert a sessions row, return the new UUID as a string."""
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO sessions (user_id, exam_id, domain) "
                "VALUES (%s, %s, %s) RETURNING id",
                (user_id, exam_id, domain),
            )
            row = await cur.fetchone()
        await conn.commit()
    return str(row[0])


async def create_exchange(
    session_id: str,
    cycle: int,
    domain: str,
    topic: str,
    challenge: dict[str, Any],
    user_answer: str,
    outcome: str,
    sage_response: str,
) -> None:
    """Append a completed cycle to the exchanges table."""
    pool = get_pool()
    async with pool.connection() as conn:
        await conn.execute(
            "INSERT INTO exchanges (session_id, cycle, domain, topic, "
            "challenge, user_answer, outcome, sage_response) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (
                session_id,
                cycle,
                domain,
                topic,
                json.dumps(challenge),
                user_answer,
                outcome,
                sage_response,
            ),
        )
        await conn.commit()


async def close_session(session_id: str) -> None:
    """Stamp the session's ended_at — fired by coach_close."""
    pool = get_pool()
    async with pool.connection() as conn:
        await conn.execute(
            "UPDATE sessions SET ended_at = %s WHERE id = %s",
            (datetime.now(timezone.utc), session_id),
        )
        await conn.commit()
