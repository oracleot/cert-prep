from __future__ import annotations

import json

from performance_repository import calculate_readiness


async def rebuild_deleted_session_progress(conn, user_id: str, exam_id: str) -> None:
    await conn.execute("DELETE FROM performance_aggregates WHERE user_id = %s AND exam_id = %s", (user_id, exam_id))
    await conn.execute(
        "INSERT INTO performance_aggregates (user_id, exam_id, domain, correct_count, total_count) "
        "SELECT s.user_id, s.exam_id, e.domain, "
        "COUNT(*) FILTER (WHERE e.outcome = 'correct'), "
        "COUNT(*) FILTER (WHERE e.outcome IN ('correct', 'incorrect')) "
        "FROM exchanges e JOIN sessions s ON s.id = e.session_id "
        "WHERE s.user_id = %s AND s.exam_id = %s AND e.review_status = 'active' "
        "GROUP BY s.user_id, s.exam_id, e.domain",
        (user_id, exam_id),
    )
    await conn.execute("DELETE FROM rex_record WHERE user_id = %s AND exam_id = %s", (user_id, exam_id))

    domains = await _active_domains(conn, user_id, exam_id)
    if not domains:
        await conn.execute("DELETE FROM readiness_scores WHERE user_id = %s AND exam_id = %s", (user_id, exam_id))
        return

    stats = await _performance_stats(conn, user_id, exam_id)
    topic_stats = await _topic_stats(conn, user_id, exam_id)
    score, breakdown = calculate_readiness(domains, stats, topic_stats)
    await conn.execute(
        "INSERT INTO readiness_scores (user_id, exam_id, score, breakdown) "
        "VALUES (%s, %s, %s, %s) "
        "ON CONFLICT (user_id, exam_id) DO UPDATE SET "
        "score = EXCLUDED.score, breakdown = EXCLUDED.breakdown, updated_at = NOW()",
        (user_id, exam_id, score, json.dumps(breakdown)),
    )


async def _performance_stats(conn, user_id: str, exam_id: str) -> dict[str, dict[str, int]]:
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT domain, correct_count, total_count FROM performance_aggregates "
            "WHERE user_id = %s AND exam_id = %s",
            (user_id, exam_id),
        )
        rows = await cur.fetchall()
    return {row[0]: {"correct_count": row[1], "total_count": row[2]} for row in rows}


async def _topic_stats(conn, user_id: str, exam_id: str) -> dict[str, dict[str, int]]:
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT e.topic, e.outcome, COUNT(*) FROM exchanges e "
            "JOIN sessions s ON s.id = e.session_id "
            "WHERE s.user_id = %s AND s.exam_id = %s "
            "AND e.review_status = 'active' "
            "GROUP BY e.topic, e.outcome",
            (user_id, exam_id),
        )
        rows = await cur.fetchall()
    stats: dict[str, dict[str, int]] = {}
    for topic, outcome, count in rows:
        entry = stats.setdefault(topic, {"correct_count": 0, "total_count": 0})
        entry["total_count"] += count
        if outcome == "correct":
            entry["correct_count"] += count
    return stats


async def _active_domains(conn, user_id: str, exam_id: str) -> list[dict]:
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT domains FROM curricula WHERE user_id = %s AND exam_id = %s AND active = TRUE "
            "ORDER BY created_at DESC LIMIT 1",
            (user_id, exam_id),
        )
        row = await cur.fetchone()
    if not row:
        return []
    value = row[0]
    return json.loads(value) if isinstance(value, str) else value or []
