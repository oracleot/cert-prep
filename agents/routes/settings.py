from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from curriculum_repository import (
    get_active_curriculum,
    list_curricula_for_user,
)
from db import get_pool, has_pool
from exam_artifacts import validate_exam_id
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
    exam_id: str | None = None
    learning_style: str


class CurriculaListRequest(BaseModel):
    user_id: str


class CurriculumSwitchRequest(BaseModel):
    user_id: str
    exam_id: str


async def _latest_exam(user_id: str) -> dict:
    run = await get_latest_onboarding(user_id)
    if not run:
        raise HTTPException(status_code=404, detail="No onboarding run found")
    return run


def _canonical_exam_name(exam_id: str) -> str:
    """Resolve canonical_name from the on-disk artifact; falls back to upper-cased id."""
    result = validate_exam_id(exam_id)
    return result.canonical_name or exam_id.upper()


@router.post("/settings/learning-style")
async def update_learning_style(req: LearningStyleRequest):
    if req.learning_style not in LEARNING_STYLES:
        raise HTTPException(status_code=422, detail="Unsupported learning style")

    if req.exam_id:
        # Caller scoped to a specific exam — resolve its canonical_name from disk.
        exam_id = req.exam_id
        exam_name = _canonical_exam_name(exam_id)
    else:
        # Fall back to the user's most-recent active exam (existing behaviour).
        latest = await _latest_exam(req.user_id)
        exam_id = latest["exam_id"]
        exam_name = latest["exam_name"]

    onboarding_id = await create_onboarding_run(
        user_id=req.user_id,
        exam_id=exam_id,
        exam_name=exam_name,
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
    if not req.exam_id:
        raise HTTPException(status_code=400, detail="exam_id is required for reset-progress")

    exam_id = req.exam_id
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


@router.post("/settings/curricula")
async def list_user_curricula(req: CurriculaListRequest):
    rows = await list_curricula_for_user(req.user_id)
    return {
        "curricula": [
            {
                "curriculum_id": row["curriculum_id"],
                "exam_id": row["exam_id"],
                "exam_name": row["exam_name"] or "",
                "learning_style": row["learning_style"] or "",
                "active": bool(row["active"]),
                "created_at": row["created_at"].isoformat() if row.get("created_at") else "",
            }
            for row in rows
        ]
    }


@router.post("/settings/curriculum-switch")
async def switch_curriculum(req: CurriculumSwitchRequest):
    """Resolve the requested exam_id and decide whether the user is ready to
    resume an existing curriculum or must re-run onboarding for that exam.

    The switcher never creates a curriculum — only onboarding does. A miss
    is signalled with `status: needs_onboarding` so the frontend can route
    the user back through `/onboarding`.
    """
    result = validate_exam_id(req.exam_id)
    if not result.accepted:
        raise HTTPException(
            status_code=400,
            detail=result.message or f"Unsupported exam_id: {req.exam_id}",
        )

    exam_id = result.exam_id
    exam_name = result.canonical_name
    active = await get_active_curriculum(req.user_id, exam_id)
    if active:
        return {
            "status": "ready",
            "exam_id": exam_id,
            "exam_name": exam_name,
            "curriculum_id": active["id"],
        }
    return {
        "status": "needs_onboarding",
        "exam_id": exam_id,
        "exam_name": exam_name,
        "redirect_to": f"/onboarding?exam={exam_id}&source=settings",
    }
