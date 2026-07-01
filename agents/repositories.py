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
    missed_criteria: list[str] | None = None,
    triggered_traps: list[str] | None = None,
    official_docs: list[str] | None = None,
    skill_builder_links: list[str] | None = None,
    lab_links: list[str] | None = None,
    response_mode: str | None = None,
    options: list[dict[str, Any]] | None = None,
    answer_key: list[str] | None = None,
    selected_labels: list[str] | None = None,
    correct_labels: list[str] | None = None,
    missed_labels: list[str] | None = None,
    incorrect_labels: list[str] | None = None,
) -> None:
    """Append a completed cycle to the exchanges table.

    Miss/resource metadata columns are additive (Phase 9.6 / 9.5) and default
    to an empty list when not provided so older callers keep working.

    Phase 11 — option-based sessions persist response_mode + options +
    answer_key alongside the challenge JSONB, and snapshot the four label
    breakdowns (selected / correct / missed / incorrect) on dedicated
    columns for fast history rendering. All new fields default to empty
    values so existing call sites keep working.
    """
    if not has_pool():
        return

    pool = get_pool()
    async with pool.connection() as conn:
        await conn.execute(
            "INSERT INTO exchanges (session_id, cycle, domain, topic, "
            "challenge, user_answer, outcome, answer_intent, sage_response, citations, concept_id, "
            "missed_criteria, triggered_traps, official_docs, skill_builder_links, lab_links, "
            "response_mode, options, answer_key, selected_labels, correct_labels, "
            "missed_labels, incorrect_labels) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULLIF(%s, ''), "
            "%s, %s, %s, %s, %s, "
            "NULLIF(%s, ''), %s, %s, %s, %s, %s, %s)",
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
                json.dumps(missed_criteria or []),
                json.dumps(triggered_traps or []),
                json.dumps(official_docs or []),
                json.dumps(skill_builder_links or []),
                json.dumps(lab_links or []),
                response_mode or "",
                json.dumps(options or []),
                json.dumps(answer_key or []),
                json.dumps(selected_labels or []),
                json.dumps(correct_labels or []),
                json.dumps(missed_labels or []),
                json.dumps(incorrect_labels or []),
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


# Re-exported here so existing `from repositories import concept_misses_for_user`
# keeps working after the Phase 11 split.
from repositories_misses import concept_misses_for_user  # noqa: E402, F401
