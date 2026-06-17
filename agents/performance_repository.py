from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from curriculum_progress import domain_readiness, topic_performance_map
from db import get_pool, has_pool


def calculate_readiness(
    domains: Sequence[Mapping[str, Any]],
    stats: dict[str, dict[str, int]],
    topic_stats: dict[str, dict[str, int]] | None = None,
) -> tuple[int, list[dict]]:
    """Top-level readiness score and per-domain breakdown.

    Each domain contributes:  weight * coverage * performance
    where coverage    = topics_attempted / topics_in_domain
          performance = correct / total on attempted topics
    Multiplying by coverage stops a single lucky answer from counting
    for the full weight of a domain.
    """
    topic_stats = topic_stats or {}
    breakdown = []
    for domain in domains:
        stat = stats.get(domain["name"], {"correct_count": 0, "total_count": 0})
        total = stat["total_count"]
        performance = stat["correct_count"] / total if total else 0
        readiness = domain_readiness(domain, stat, topic_stats)
        contribution = domain["weight"] * readiness
        breakdown.append({
            "domain": domain["name"],
            "weight": domain["weight"],
            "correct_count": stat["correct_count"],
            "total_count": total,
            "performance_score": round(performance, 2),
            "readiness_contribution": round(contribution),
        })
    return round(sum(item["readiness_contribution"] for item in breakdown)), breakdown


async def _domain_stats(user_id: str, exam_id: str) -> dict[str, dict[str, int]]:
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


async def record_session_history(
    user_id: str,
    exam_id: str,
    history: Sequence[Mapping[str, Any]],
) -> None:
    if not has_pool():
        return

    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
    for exchange in history:
        if exchange.get("outcome") not in {"correct", "incorrect"}:
            continue
        domain = exchange.get("domain")
        if not domain:
            continue
        counts[domain]["total"] += 1
        if exchange["outcome"] == "correct":
            counts[domain]["correct"] += 1

    if not counts:
        return

    pool = get_pool()
    async with pool.connection() as conn:
        for domain, result in counts.items():
            await conn.execute(
                "INSERT INTO performance_aggregates "
                "(user_id, exam_id, domain, correct_count, total_count) "
                "VALUES (%s, %s, %s, %s, %s) "
                "ON CONFLICT (user_id, exam_id, domain) DO UPDATE SET "
                "correct_count = performance_aggregates.correct_count + EXCLUDED.correct_count, "
                "total_count = performance_aggregates.total_count + EXCLUDED.total_count, "
                "updated_at = NOW()",
                (user_id, exam_id, domain, result["correct"], result["total"]),
            )
        await conn.commit()


async def persist_readiness_score(
    user_id: str,
    exam_id: str,
    domains: Sequence[Mapping[str, Any]],
) -> None:
    if not has_pool() or not domains:
        return

    stats = await _domain_stats(user_id, exam_id)
    topic_stats = await topic_performance_map(user_id, exam_id)
    score, breakdown = calculate_readiness(domains, stats, topic_stats)
    pool = get_pool()
    async with pool.connection() as conn:
        await conn.execute(
            "INSERT INTO readiness_scores (user_id, exam_id, score, breakdown) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (user_id, exam_id) DO UPDATE SET "
            "score = EXCLUDED.score, breakdown = EXCLUDED.breakdown, updated_at = NOW()",
            (user_id, exam_id, score, json.dumps(breakdown)),
        )
        await conn.commit()


async def read_readiness_score(user_id: str, exam_id: str) -> dict[str, Any] | None:
    if not has_pool():
        return None

    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT score, breakdown FROM readiness_scores WHERE user_id = %s AND exam_id = %s",
                (user_id, exam_id),
            )
            row = await cur.fetchone()
    if not row:
        return None
    return {"score": row[0], "breakdown": json.loads(row[1]) if isinstance(row[1], str) else row[1]}


async def record_rex_result(user_id: str, exam_id: str, outcome: str) -> None:
    if not has_pool() or outcome not in {"correct", "incorrect"}:
        return

    user_wins = 1 if outcome == "correct" else 0
    rex_wins = 1 if outcome == "incorrect" else 0
    pool = get_pool()
    async with pool.connection() as conn:
        await conn.execute(
            "INSERT INTO rex_record (user_id, exam_id, user_wins, rex_wins) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (user_id, exam_id) DO UPDATE SET "
            "user_wins = rex_record.user_wins + EXCLUDED.user_wins, "
            "rex_wins = rex_record.rex_wins + EXCLUDED.rex_wins, updated_at = NOW()",
            (user_id, exam_id, user_wins, rex_wins),
        )
        await conn.commit()


async def read_rex_record(user_id: str, exam_id: str) -> dict[str, int]:
    if not has_pool():
        return {"user_wins": 0, "rex_wins": 0}

    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT user_wins, rex_wins FROM rex_record WHERE user_id = %s AND exam_id = %s",
                (user_id, exam_id),
            )
            row = await cur.fetchone()
    if row:
        return {"user_wins": row[0], "rex_wins": row[1]}

    stats = await _domain_stats(user_id, exam_id)
    correct = sum(item["correct_count"] for item in stats.values())
    total = sum(item["total_count"] for item in stats.values())
    return {"user_wins": correct, "rex_wins": total - correct}
