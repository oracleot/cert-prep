from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from db import get_pool, has_pool


def _local_date(tz_name: str) -> date:
    try:
        tz = ZoneInfo(tz_name or "UTC")
    except ZoneInfoNotFoundError:
        tz = timezone.utc
    return datetime.now(tz).date()


def _visible_streak(streak: int, last_completed_on: date | None, today: date) -> int:
    if not last_completed_on:
        return 0
    if last_completed_on < today - timedelta(days=1):
        return 0
    return streak


async def record_completed_session(
    user_id: str,
    exam_id: str,
    timezone_name: str = "UTC",
) -> None:
    if not has_pool():
        return

    today = _local_date(timezone_name)
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT current_streak, last_completed_on FROM session_streaks "
                "WHERE user_id = %s AND exam_id = %s FOR UPDATE",
                (user_id, exam_id),
            )
            row = await cur.fetchone()

        if not row:
            next_streak = 1
        elif row[1] == today:
            next_streak = row[0]
        elif row[1] == today - timedelta(days=1):
            next_streak = row[0] + 1
        else:
            next_streak = 1

        await conn.execute(
            "INSERT INTO session_streaks "
            "(user_id, exam_id, current_streak, last_completed_on) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (user_id, exam_id) DO UPDATE SET "
            "current_streak = EXCLUDED.current_streak, "
            "last_completed_on = EXCLUDED.last_completed_on, updated_at = NOW()",
            (user_id, exam_id, next_streak, today),
        )
        await conn.commit()


async def read_session_streak(
    user_id: str,
    exam_id: str,
    timezone_name: str = "UTC",
) -> dict[str, int | str | None]:
    if not has_pool():
        return {"current_streak": 0, "last_completed_on": None}

    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT current_streak, last_completed_on FROM session_streaks "
                "WHERE user_id = %s AND exam_id = %s",
                (user_id, exam_id),
            )
            row = await cur.fetchone()

    if not row:
        return {"current_streak": 0, "last_completed_on": None}

    today = _local_date(timezone_name)
    streak = _visible_streak(row[0], row[1], today)
    return {"current_streak": streak, "last_completed_on": row[1].isoformat()}
