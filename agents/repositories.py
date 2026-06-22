# Application table CRUD: sessions and exchanges.
# LangGraph checkpointer tables are managed separately by
# AsyncPostgresSaver.setup() in db.py.

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from db import get_pool, has_pool


async def create_session(
    user_id: str,
    exam_id: str,
    domain: str,
    topic: str,
    curriculum_id: str = "",
    concept_id: str | None = None,
) -> str:
    """Insert a sessions row, return the new UUID as a string."""
    if not has_pool():
        return ""

    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO sessions (user_id, exam_id, domain, topic, curriculum_id, concept_id) "
                "VALUES (%s, %s, %s, %s, NULLIF(%s, '')::uuid, NULLIF(%s, '')) RETURNING id",
                (user_id, exam_id, domain, topic, curriculum_id, concept_id or ""),
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
    answer_intent: str,
    sage_response: str,
    citations: list[Any],
    concept_id: str | None = None,
) -> None:
    """Append a completed cycle to the exchanges table."""
    if not has_pool():
        return

    pool = get_pool()
    async with pool.connection() as conn:
        await conn.execute(
            "INSERT INTO exchanges (session_id, cycle, domain, topic, "
            "challenge, user_answer, outcome, answer_intent, sage_response, citations, concept_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULLIF(%s, ''))",
            (
                session_id,
                cycle,
                domain,
                topic,
                json.dumps(challenge),
                user_answer,
                outcome,
                answer_intent,
                sage_response,
                json.dumps(citations),
                concept_id or "",
            ),
        )
        await conn.commit()


async def exchange_history_for_user(exam_id: str, user_id: str) -> list[dict[str, Any]]:
    """Return prior exchanges for user across all their sessions for the exam.

    Returns rows with ``concept_id`` (may be NULL for pre-9.3 exchanges) and
    ``outcome``.  Safe to call when exchanges.concept_id is entirely NULL.
    """
    if not has_pool():
        return []

    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """SELECT e.concept_id, e.outcome
                   FROM exchanges e
                   JOIN sessions s ON s.id = e.session_id
                   WHERE s.user_id = %s AND s.exam_id = %s
                   ORDER BY e.created_at DESC""",
                (user_id, exam_id),
            )
            rows = await cur.fetchall()
    return [{"concept_id": row[0], "outcome": row[1]} for row in rows]


async def close_session(session_id: str) -> None:
    """Stamp the session's ended_at — fired by coach_close."""
    if not has_pool():
        return

    pool = get_pool()
    async with pool.connection() as conn:
        await conn.execute(
            "UPDATE sessions SET ended_at = %s WHERE id = %s",
            (datetime.now(timezone.utc), session_id),
        )
        await conn.commit()
