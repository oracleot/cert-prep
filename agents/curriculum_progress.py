from __future__ import annotations

from typing import Any

from curriculum_topics import topic_label
from db import get_pool, has_pool


async def performance_map(user_id: str, exam_id: str) -> dict[str, dict[str, int]]:
    if not has_pool():
        return {}
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT domain, correct_count, total_count FROM performance_aggregates "
                "WHERE user_id = %s AND exam_id = %s",
                (user_id, exam_id),
            )
            rows = await cur.fetchall()
    return {row[0]: {"correct_count": row[1], "total_count": row[2]} for row in rows}


async def topic_performance_map(user_id: str, exam_id: str) -> dict[str, dict[str, int]]:
    if not has_pool():
        return {}
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT e.topic, e.outcome, COUNT(*) FROM exchanges e "
                "JOIN sessions s ON s.id = e.session_id "
                "WHERE s.user_id = %s AND s.exam_id = %s "
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


def domain_overview(
    domains: list[dict],
    domain_stats: dict[str, dict[str, int]],
    topic_stats: dict[str, dict[str, int]],
) -> list[dict]:
    overview = []
    for domain in sorted(domains, key=lambda item: item.get("study_order", 99)):
        stat = domain_stats.get(domain["name"], {"correct_count": 0, "total_count": 0})
        total = stat["total_count"]
        topics = domain.get("topics", [])
        topic_count = max(len(topics), 1)
        covered_topics = _covered_topic_count(topics, topic_stats)
        performance = stat["correct_count"] / total if total else 0
        overview.append({
            **domain,
            "correct_count": stat["correct_count"],
            "total_count": total,
            "performance_score": round(performance, 2),
            "topic_count": topic_count,
            "covered_topic_count": covered_topics,
            "completion_percent": min(100, round((covered_topics / topic_count) * 100)),
        })
    return overview


def _covered_topic_count(topics: list[Any], stats: dict[str, dict[str, int]]) -> int:
    return sum(
        1 for topic in topics
        if stats.get(topic_label(topic), {}).get("correct_count", 0) > 0
    )
