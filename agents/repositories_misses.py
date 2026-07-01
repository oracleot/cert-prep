# Phase 9.6 concept-miss audit query, kept out of repositories.py so the
# core CRUD file stays under the 200-line hard rule. The same
# ``has_pool`` / ``get_pool`` pattern is used; no behavioural difference.

from __future__ import annotations

from typing import Any

from db import get_pool, has_pool


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


__all__ = ["concept_misses_for_user"]