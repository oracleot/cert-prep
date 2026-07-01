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


async def concept_misses_for_user(
    exam_id: str,
    user_id: str,
    concept_id: str | None = None,
) -> list[dict[str, Any]]:
    """Internal concept-miss audit (Phase 9.6).

    Returns active exchanges for ``user_id``/``exam_id`` (optionally scoped to
    a single ``concept_id``) that carry a non-empty ``missed_criteria`` or
    ``triggered_traps`` payload. Excluded / pending-review / dismissed
    exchanges are skipped — readiness math is unaffected, this feed is for
    future routing and coaching use only.
    """
    if not has_pool():
        return []

    params: list[Any] = [user_id, exam_id]
    sql = (
        "SELECT e.id, e.concept_id, e.domain, e.topic, e.cycle, e.outcome, "
        "e.missed_criteria, e.triggered_traps, e.created_at "
        "FROM exchanges e "
        "JOIN sessions s ON s.id = e.session_id "
        "WHERE s.user_id = %s AND s.exam_id = %s "
        "AND e.review_status = 'active' "
        "AND (jsonb_array_length(e.missed_criteria) > 0 "
        "     OR jsonb_array_length(e.triggered_traps) > 0)"
    )
    if concept_id:
        sql += " AND e.concept_id = %s"
        params.append(concept_id)
    sql += " ORDER BY e.created_at DESC"

    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()
    return [
        {
            "exchange_id": row[0],
            "concept_id": row[1],
            "domain": row[2],
            "topic": row[3],
            "cycle": row[4],
            "outcome": row[5],
            "missed_criteria": row[6] or [],
            "triggered_traps": row[7] or [],
            "created_at": row[8],
        }
        for row in rows
    ]
