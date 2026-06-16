from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from blueprint import DEFAULT_EXAM_ID
from curriculum_repository import dashboard_summary, progress_map

router = APIRouter()


class UserScopedRequest(BaseModel):
    user_id: str
    exam_id: str = DEFAULT_EXAM_ID


@router.post("/dashboard/summary")
async def summary(req: UserScopedRequest):
    return await dashboard_summary(req.user_id, req.exam_id)


@router.post("/progress")
async def progress(req: UserScopedRequest):
    return await progress_map(req.user_id, req.exam_id)
