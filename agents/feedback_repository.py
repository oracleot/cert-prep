from __future__ import annotations

from typing import Any

from db import get_pool, has_pool

FEEDBACK_TYPES = {"factual_error", "bad_source", "confusing_explanation"}


def _feedback(row) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "feedback_type": row[0],
        "status": row[1],
        "excludes_metrics": bool(row[2]),
        "review_status": row[3],
    }


async def feedback_for_cycle(session_id: str, cycle: int) -> dict[str, Any] | None:
    if not has_pool() or not session_id:
        return None
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT f.feedback_type, f.status, f.excludes_metrics, e.review_status "
                "FROM sage_feedback f JOIN exchanges e ON e.id = f.exchange_id "
                "WHERE f.session_id = %s AND f.cycle = %s",
                (session_id, cycle),
            )
            return _feedback(await cur.fetchone())


async def feedback_by_cycle(session_id: str) -> dict[int, dict[str, Any]]:
    if not has_pool() or not session_id:
        return {}
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT f.cycle, f.feedback_type, f.status, f.excludes_metrics, e.review_status "
                "FROM sage_feedback f JOIN exchanges e ON e.id = f.exchange_id "
                "WHERE f.session_id = %s",
                (session_id,),
            )
            rows = await cur.fetchall()
    return {row[0]: cast_feedback(row[1:]) for row in rows}


async def create_sage_feedback(
    thread_id: str,
    session_id: str,
    cycle: int,
    feedback_type: str,
    comment: str,
) -> dict[str, Any]:
    if not has_pool():
        raise RuntimeError("Persistence is unavailable")
    if feedback_type not in FEEDBACK_TYPES:
        raise ValueError("Unsupported feedback type")
    trimmed = comment.strip()
    if len(trimmed) < 10 or len(trimmed) > 1000:
        raise ValueError("Comment must be between 10 and 1000 characters")

    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT f.feedback_type, f.status, f.excludes_metrics, e.review_status "
                "FROM sage_feedback f JOIN exchanges e ON e.id = f.exchange_id "
                "WHERE f.session_id = %s AND f.cycle = %s",
                (session_id, cycle),
            )
            existing = _feedback(await cur.fetchone())
            if existing:
                return existing

            await cur.execute(
                "SELECT e.id, e.domain, e.topic, e.outcome, e.review_status, s.user_id, s.exam_id "
                "FROM exchanges e JOIN sessions s ON s.id = e.session_id "
                "WHERE e.session_id = %s AND e.cycle = %s FOR UPDATE OF e",
                (session_id, cycle),
            )
            row = await cur.fetchone()
            if not row:
                raise LookupError("Exchange not found")

            exchange_id, domain, topic, outcome, review_status, user_id, exam_id = row
            excludes_metrics = feedback_type == "factual_error"
            reversed_metrics = excludes_metrics and review_status == "active"
            if reversed_metrics:
                await _reverse_metrics(conn, user_id, exam_id, domain, outcome)
                await conn.execute(
                    "UPDATE exchanges SET review_status = 'excluded_pending_review' WHERE id = %s",
                    (exchange_id,),
                )

            await cur.execute(
                "INSERT INTO sage_feedback (session_id, exchange_id, thread_id, user_id, exam_id, "
                "domain, topic, cycle, feedback_type, comment, excludes_metrics, metrics_reversed_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                "CASE WHEN %s THEN NOW() ELSE NULL END) "
                "RETURNING feedback_type, status, excludes_metrics",
                (
                    session_id,
                    exchange_id,
                    thread_id,
                    user_id,
                    exam_id,
                    domain,
                    topic,
                    cycle,
                    feedback_type,
                    trimmed,
                    excludes_metrics,
                    reversed_metrics,
                ),
            )
            created = await cur.fetchone()
            if not created:
                raise RuntimeError("Feedback row was not returned")
        await conn.commit()
    return cast_feedback((*created, "excluded_pending_review" if reversed_metrics else review_status))


def cast_feedback(row) -> dict[str, Any]:
    feedback = _feedback(row)
    if feedback is None:
        raise RuntimeError("Feedback row was not returned")
    return feedback


async def _reverse_metrics(conn, user_id: str, exam_id: str, domain: str, outcome: str) -> None:
    correct_delta = 1 if outcome == "correct" else 0
    rex_delta = 1 if outcome == "incorrect" else 0
    await conn.execute(
        "UPDATE performance_aggregates SET correct_count = GREATEST(correct_count - %s, 0), "
        "total_count = GREATEST(total_count - 1, 0), updated_at = NOW() "
        "WHERE user_id = %s AND exam_id = %s AND domain = %s",
        (correct_delta, user_id, exam_id, domain),
    )
    await conn.execute(
        "UPDATE rex_record SET user_wins = GREATEST(user_wins - %s, 0), "
        "rex_wins = GREATEST(rex_wins - %s, 0), updated_at = NOW() "
        "WHERE user_id = %s AND exam_id = %s",
        (correct_delta, rex_delta, user_id, exam_id),
    )
