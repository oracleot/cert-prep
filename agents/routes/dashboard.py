from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from curriculum_repository import (
    dashboard_summary,
    get_active_curriculum,
    progress_map,
)
from exam_artifacts import validate_exam_id
from onboarding_repository import get_latest_onboarding

router = APIRouter()


class UserScopedRequest(BaseModel):
    user_id: str
    exam_id: str | None = None
    timezone: str = "UTC"


async def _exam_id_for(req: UserScopedRequest) -> str:
    # INTENTIONAL FALLBACK: this `exam_id`-less resolution is load-bearing for
    # the post-build activation path in app/onboarding/use-onboarding.ts:loadPlan,
    # where the just-built curriculum is discovered via /dashboard/summary BEFORE
    # `useActiveCurriculum()` has been populated. Do NOT remove without also
    # rewriting that activation path.
    if req.exam_id:
        return req.exam_id
    run = await get_latest_onboarding(req.user_id)
    return run["exam_id"] if run else "dva-c02"


def _canonical_exam_name(exam_id: str) -> str:
    """Resolve canonical_name from the on-disk artifact; falls back to upper-cased id."""
    result = validate_exam_id(exam_id)
    return result.canonical_name or exam_id.upper()


@router.post("/dashboard/summary")
async def summary(req: UserScopedRequest):
    exam_id = await _exam_id_for(req)
    result = await dashboard_summary(req.user_id, exam_id, req.timezone)
    # Enrich with curriculum_id and exam_name so the frontend can render the
    # switcher affordance and the exam header without a second roundtrip.
    curriculum = await get_active_curriculum(req.user_id, exam_id)
    result["curriculum_id"] = curriculum["id"] if curriculum else ""
    result["exam_name"] = _canonical_exam_name(exam_id)
    return result


@router.post("/progress")
async def progress(req: UserScopedRequest):
    return await progress_map(req.user_id, await _exam_id_for(req))
