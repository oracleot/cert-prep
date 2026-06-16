from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from curriculum_repository import dashboard_summary, progress_map
from onboarding_repository import get_latest_onboarding

router = APIRouter()


class UserScopedRequest(BaseModel):
    user_id: str
    exam_id: str | None = None
    timezone: str = "UTC"


async def _exam_id_for(req: UserScopedRequest) -> str:
    if req.exam_id:
        return req.exam_id
    run = await get_latest_onboarding(req.user_id)
    return run["exam_id"] if run else "dva-c02"


@router.post("/dashboard/summary")
async def summary(req: UserScopedRequest):
    return await dashboard_summary(req.user_id, await _exam_id_for(req), req.timezone)


@router.post("/progress")
async def progress(req: UserScopedRequest):
    return await progress_map(req.user_id, await _exam_id_for(req))
