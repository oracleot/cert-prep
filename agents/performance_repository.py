from __future__ import annotations

from collections import defaultdict

from db import get_pool, has_pool


async def record_session_history(user_id: str, exam_id: str, history: list[dict]) -> None:
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
