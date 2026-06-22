from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db import get_pool, has_pool
from onboarding_repository import (
    add_feed_event,
    create_onboarding_run,
    get_latest_onboarding,
)

router = APIRouter()

LEARNING_STYLES = {"pressure_drills", "guided_explanations", "mixed_review"}


class UserSettingsRequest(BaseModel):
    user_id: str
    exam_id: str | None = None


class LearningStyleRequest(BaseModel):
    user_id: str
    learning_style: str


async def _latest_exam(user_id: str) -> dict:
    run = await get_latest_onboarding(user_id)
    if not run:
        raise HTTPException(status_code=404, detail="No onboarding run found")
    return run


@router.post("/settings/learning-style")
async def update_learning_style(req: LearningStyleRequest):
    if req.learning_style not in LEARNING_STYLES:
        raise HTTPException(status_code=422, detail="Unsupported learning style")

    latest = await _latest_exam(req.user_id)
    onboarding_id = await create_onboarding_run(
        user_id=req.user_id,
        exam_id=latest["exam_id"],
        exam_name=latest["exam_name"],
        learning_style=req.learning_style,
    )
    if not onboarding_id:
        raise HTTPException(status_code=503, detail="Onboarding persistence is unavailable")

    await add_feed_event(
        onboarding_id,
        "Settings",
        "complete",
        "Learning style changed. Rebuilding your curriculum route.",
    )
    return {"ok": True, "onboarding_id": onboarding_id}


@router.post("/settings/reset-progress")
async def reset_progress(req: UserSettingsRequest):
    if not has_pool():
        raise HTTPException(status_code=503, detail="Persistence is unavailable")

    exam_id = req.exam_id or (await _latest_exam(req.user_id))["exam_id"]
    pool = get_pool()
    async with pool.connection() as conn:
        params = (req.user_id, exam_id)
        await conn.execute("DELETE FROM sessions WHERE user_id = %s AND exam_id = %s", params)
        await conn.execute("DELETE FROM performance_aggregates WHERE user_id = %s AND exam_id = %s", params)
        await conn.execute("DELETE FROM readiness_scores WHERE user_id = %s AND exam_id = %s", params)
        await conn.execute("DELETE FROM rex_record WHERE user_id = %s AND exam_id = %s", params)
        await conn.execute("DELETE FROM session_streaks WHERE user_id = %s AND exam_id = %s", params)
        await conn.execute("DELETE FROM domain_difficulty_progress WHERE user_id = %s AND exam_id = %s", params)
        await conn.commit()
    return {"ok": True, "exam_id": exam_id}
