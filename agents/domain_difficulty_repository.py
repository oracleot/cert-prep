from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from db import get_pool, has_pool

DIFFICULTIES = ("easy", "medium", "hard")
ACCURACY_THRESHOLD = 0.8
HIGH_STREAK_TO_UPGRADE = 3
LOW_STREAK_TO_DOWNGRADE = 2


async def read_domain_difficulties(user_id: str, exam_id: str) -> dict[str, str]:
    if not has_pool():
        return {}

    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT domain, difficulty FROM domain_difficulty_progress "
                "WHERE user_id = %s AND exam_id = %s",
                (user_id, exam_id),
            )
            rows = await cur.fetchall()
    return {row[0]: _difficulty(row[1]) for row in rows}


async def record_domain_difficulty_sessions(
    user_id: str,
    exam_id: str,
    history: Sequence[Mapping[str, Any]],
) -> None:
    if not has_pool():
        return

    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
    for exchange in history:
        outcome = exchange.get("outcome")
        domain = exchange.get("domain")
        if outcome not in {"correct", "incorrect"} or not domain:
            continue
        counts[domain]["total"] += 1
        if outcome == "correct":
            counts[domain]["correct"] += 1

    if not counts:
        return

    pool = get_pool()
    async with pool.connection() as conn:
        for domain, result in counts.items():
            difficulty, high_streak, low_streak = await _current_progress(conn, user_id, exam_id, domain)
            difficulty, high_streak, low_streak = _next_progress(
                difficulty,
                high_streak,
                low_streak,
                result["correct"] / result["total"],
            )
            await conn.execute(
                "INSERT INTO domain_difficulty_progress "
                "(user_id, exam_id, domain, difficulty, high_accuracy_streak, low_accuracy_streak) "
                "VALUES (%s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (user_id, exam_id, domain) DO UPDATE SET "
                "difficulty = EXCLUDED.difficulty, "
                "high_accuracy_streak = EXCLUDED.high_accuracy_streak, "
                "low_accuracy_streak = EXCLUDED.low_accuracy_streak, updated_at = NOW()",
                (user_id, exam_id, domain, difficulty, high_streak, low_streak),
            )
        await conn.commit()


async def _current_progress(conn, user_id: str, exam_id: str, domain: str) -> tuple[str, int, int]:
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT difficulty, high_accuracy_streak, low_accuracy_streak "
            "FROM domain_difficulty_progress "
            "WHERE user_id = %s AND exam_id = %s AND domain = %s",
            (user_id, exam_id, domain),
        )
        row = await cur.fetchone()
    if not row:
        return "easy", 0, 0
    return _difficulty(row[0]), row[1], row[2]


def _next_progress(difficulty: str, high_streak: int, low_streak: int, accuracy: float) -> tuple[str, int, int]:
    if accuracy > ACCURACY_THRESHOLD:
        high_streak += 1
        low_streak = 0
        if high_streak >= HIGH_STREAK_TO_UPGRADE:
            return _shift(difficulty, 1), 0, 0
        return difficulty, high_streak, low_streak

    if accuracy < ACCURACY_THRESHOLD:
        low_streak += 1
        high_streak = 0
        if low_streak >= LOW_STREAK_TO_DOWNGRADE:
            return _shift(difficulty, -1), 0, 0
        return difficulty, high_streak, low_streak

    return difficulty, 0, 0


def _shift(difficulty: str, offset: int) -> str:
    rank = max(0, min(DIFFICULTIES.index(_difficulty(difficulty)) + offset, len(DIFFICULTIES) - 1))
    return DIFFICULTIES[rank]


def _difficulty(value: str) -> str:
    return value if value in DIFFICULTIES else "easy"
