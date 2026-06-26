"""Curriculum CRUD against the `curricula` table.

Domain shaping and selection live in `curriculum_planning`; this module
only reads and writes rows.
"""

from __future__ import annotations

import json
from typing import Any

from db import get_pool, has_pool


async def create_curriculum(
    user_id: str,
    exam_id: str,
    onboarding_id: str,
    domains: list[dict],
) -> str:
    if not has_pool():
        return ""

    pool = get_pool()
    async with pool.connection() as conn:
        await conn.execute(
            "UPDATE curricula SET active = FALSE WHERE user_id = %s AND exam_id = %s",
            (user_id, exam_id),
        )
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO curricula (user_id, exam_id, onboarding_run_id, domains, active) "
                "VALUES (%s, %s, %s, %s, TRUE) RETURNING id",
                (user_id, exam_id, onboarding_id, json.dumps(domains)),
            )
            row = await cur.fetchone()
        await conn.commit()
    if not row:
        return ""
    return str(row[0])


async def get_active_curriculum(user_id: str, exam_id: str) -> dict[str, Any] | None:
    if not has_pool():
        return None

    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id, domains FROM curricula WHERE user_id = %s AND exam_id = %s "
                "AND active = TRUE ORDER BY created_at DESC LIMIT 1",
                (user_id, exam_id),
            )
            row = await cur.fetchone()
    if not row:
        return None
    return {"id": str(row[0]), "domains": _coerce_domains(row[1])}


async def list_curricula_for_user(user_id: str) -> list[dict[str, Any]]:
    """List every curriculum for a user, newest first.

    LEFT JOIN to onboarding_runs surfaces `exam_name` and `learning_style`
    from the originating onboarding run. Both fields are nullable because
    `curricula.onboarding_run_id` allows NULL (ON DELETE SET NULL) — in
    practice every curriculum has one, but the JOIN reflects the FK shape.
    """
    if not has_pool():
        return []
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT c.id, c.exam_id, o.exam_name, o.learning_style, c.active, c.created_at "
                "FROM curricula c LEFT JOIN onboarding_runs o ON c.onboarding_run_id = o.id "
                "WHERE c.user_id = %s ORDER BY c.created_at DESC",
                (user_id,),
            )
            rows = await cur.fetchall()
    return [
        {
            "curriculum_id": str(row[0]),
            "exam_id": row[1],
            "exam_name": row[2],
            "learning_style": row[3],
            "active": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]


def _coerce_domains(value: Any) -> list[dict]:
    return json.loads(value) if isinstance(value, str) else value


# Re-exports for backward compatibility with callers that still import
# planning/composition helpers from this module. Imported at the bottom so
# the planning module can import `get_active_curriculum` (defined above)
# without tripping on a circular import.
from curriculum_planning import (  # noqa: E402,F401
    active_domains_for,
    build_curriculum,
    choose_rechallenge_target,
    choose_today_target,
    dashboard_summary,
    progress_map,
)
