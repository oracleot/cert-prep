from __future__ import annotations

import json
from typing import Any

from db import get_pool, has_pool


async def create_onboarding_run(
    user_id: str,
    exam_id: str,
    exam_name: str,
    learning_style: str,
) -> str:
    if not has_pool():
        return ""

    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO onboarding_runs "
                "(user_id, exam_id, exam_name, learning_style, status, step) "
                "VALUES (%s, %s, %s, %s, 'queued', 'agent_feed') RETURNING id",
                (user_id, exam_id, exam_name, learning_style),
            )
            row = await cur.fetchone()
        await conn.commit()
    return str(row[0])


async def add_feed_event(
    onboarding_id: str,
    agent: str,
    status: str,
    message: str,
) -> None:
    if not has_pool() or not onboarding_id:
        return

    pool = get_pool()
    async with pool.connection() as conn:
        await conn.execute(
            "INSERT INTO agent_feed_events "
            "(onboarding_run_id, agent, status, message) VALUES (%s, %s, %s, %s)",
            (onboarding_id, agent, status, message),
        )
        await conn.commit()


async def list_feed_events(onboarding_id: str, after_id: int = 0) -> list[dict[str, Any]]:
    if not has_pool():
        return []

    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id, agent, status, message, created_at FROM agent_feed_events "
                "WHERE onboarding_run_id = %s AND id > %s ORDER BY id ASC",
                (onboarding_id, after_id),
            )
            rows = await cur.fetchall()
    return [
        {
            "id": row[0],
            "agent": row[1],
            "status": row[2],
            "message": row[3],
            "created_at": row[4].isoformat(),
        }
        for row in rows
    ]


async def get_onboarding_run(onboarding_id: str) -> dict[str, Any] | None:
    if not has_pool():
        return None

    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id, user_id, exam_id, exam_name, learning_style, status, "
                "step, blueprint, curriculum_id FROM onboarding_runs WHERE id = %s",
                (onboarding_id,),
            )
            row = await cur.fetchone()
    return _run_from_row(row) if row else None


async def get_latest_onboarding(user_id: str) -> dict[str, Any] | None:
    if not has_pool():
        return None

    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id, user_id, exam_id, exam_name, learning_style, status, "
                "step, blueprint, curriculum_id FROM onboarding_runs "
                "WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                (user_id,),
            )
            row = await cur.fetchone()
    return _run_from_row(row) if row else None


async def get_learning_style(user_id: str) -> str:
    """Read the most recent learning_style for a user. Returns "" when absent
    or no pool — callers must default to 'mixed_review' on empty."""
    if not has_pool():
        return ""
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT learning_style FROM onboarding_runs "
                "WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                (user_id,),
            )
            row = await cur.fetchone()
    return row[0] if row and row[0] else ""


async def update_run_status(onboarding_id: str, status: str, step: str) -> None:
    if not has_pool():
        return

    pool = get_pool()
    async with pool.connection() as conn:
        await conn.execute(
            "UPDATE onboarding_runs SET status = %s, step = %s, updated_at = NOW() "
            "WHERE id = %s",
            (status, step, onboarding_id),
        )
        await conn.commit()


async def save_blueprint(onboarding_id: str, blueprint: list[dict]) -> None:
    if not has_pool():
        return

    pool = get_pool()
    async with pool.connection() as conn:
        await conn.execute(
            "UPDATE onboarding_runs SET blueprint = %s, status = 'blueprint_complete', "
            "step = 'agent_feed', updated_at = NOW() WHERE id = %s",
            (json.dumps(blueprint), onboarding_id),
        )
        await conn.commit()


async def complete_onboarding(onboarding_id: str, curriculum_id: str) -> None:
    if not has_pool():
        return

    pool = get_pool()
    async with pool.connection() as conn:
        await conn.execute(
            "UPDATE onboarding_runs SET curriculum_id = %s, status = 'complete', "
            "step = 'plan_reveal', updated_at = NOW(), completed_at = NOW() WHERE id = %s",
            (curriculum_id, onboarding_id),
        )
        await conn.commit()


async def fail_onboarding(onboarding_id: str, message: str) -> None:
    await update_run_status(onboarding_id, "failed", "agent_feed")
    await add_feed_event(onboarding_id, "Onboarding", "failed", message)


def _run_from_row(row) -> dict[str, Any]:
    blueprint = row[7]
    if isinstance(blueprint, str):
        blueprint = json.loads(blueprint)
    return {
        "id": str(row[0]),
        "user_id": row[1],
        "exam_id": row[2],
        "exam_name": row[3],
        "learning_style": row[4],
        "status": row[5],
        "step": row[6],
        "blueprint": blueprint,
        "curriculum_id": str(row[8]) if row[8] else None,
    }
