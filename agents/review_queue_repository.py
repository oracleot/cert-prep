"""Review-queue queries for the spaced-review feature.

Returns per-concept rows from the ``exchanges`` table joined with
``sessions``, giving each concept the most-recent outcome / timestamp seen
for a given ``(user_id, exam_id)`` pair. The selection rule that decides
which concepts are "due" lives in Python so the criteria can evolve
without a schema change.
"""
from __future__ import annotations

from typing import Any

from db import get_pool, has_pool


async def review_queue_for_user(
    user_id: str,
    exam_id: str,
    limit: int = 10,
    seen_within_days: int = 2,
    due_after_days: int = 3,
) -> list[dict[str, Any]]:
    """Return the filtered, sorted review-queue for ``(user_id, exam_id)``.

    Each row is the most-recent exchange for one concept::

        {concept_id, last_outcome, last_seen_at, days_since_seen}

    Selection rule — keep rows where::

        (last_outcome == 'incorrect'
            AND days_since_seen <= seen_within_days)
        OR (days_since_seen IS NULL
            OR days_since_seen >= due_after_days)

    Rows are sorted stale-then-wrong:
    ``(days_since_seen IS NULL) DESC, days_since_seen DESC,
    (last_outcome='incorrect') DESC``.

    The function returns the full filtered+sorted list. The caller is
    expected to truncate to ``limit`` itself so it can report
    ``total_due = len(result)`` as the pre-cap count. The ``limit`` arg is
    kept on the signature for API symmetry but is not applied here.
    """
    if not has_pool():
        return []

    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """SELECT DISTINCT ON (e.concept_id)
                       e.concept_id,
                       e.outcome AS last_outcome,
                       e.created_at AS last_seen_at,
                       EXTRACT(DAY FROM (NOW() - e.created_at))::int AS days_since_seen
                   FROM exchanges e
                   JOIN sessions s ON s.id = e.session_id
                   WHERE s.user_id = %s AND s.exam_id = %s
                   ORDER BY e.concept_id, e.created_at DESC""",
                (user_id, exam_id),
            )
            rows = await cur.fetchall()

    enriched: list[dict[str, Any]] = []
    for concept_id, last_outcome, last_seen_at, days_since_seen in rows:
        enriched.append(
            {
                "concept_id": concept_id,
                "last_outcome": last_outcome,
                "last_seen_at": last_seen_at,
                "days_since_seen": days_since_seen,
            }
        )

    def _is_due(item: dict[str, Any]) -> bool:
        dss = item["days_since_seen"]
        if item["last_outcome"] == "incorrect" and (dss is None or dss <= seen_within_days):
            return True
        if dss is None or dss >= due_after_days:
            return True
        return False

    due = [item for item in enriched if _is_due(item)]
    # Postgres-style: NULLS FIRST, then days_since_seen DESC, then wrong
    # first. reverse=True on (is_null, -dss, ==incorrect) gives:
    #   - is_null: None -> 1 -> sorts first under reverse
    #   - -dss:    larger dss -> more-negative -> sorts first under reverse
    #   - ==inc:   True -> 1 -> sorts first under reverse (wrong beats right)
    due.sort(
        key=lambda item: (
            item["days_since_seen"] is None,
            -(item["days_since_seen"] or 0),
            item["last_outcome"] == "incorrect",
        ),
        reverse=True,
    )
    return due