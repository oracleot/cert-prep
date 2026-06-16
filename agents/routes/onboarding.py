from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from blueprint import DEFAULT_EXAM_ID
from curriculum_repository import get_active_curriculum
from exam_artifacts import validate_exam_id
from onboarding_repository import (
    add_feed_event,
    create_onboarding_run,
    get_latest_onboarding,
    get_onboarding_run,
    list_feed_events,
)

router = APIRouter()


class OnboardingStartRequest(BaseModel):
    user_id: str
    exam_name: str
    learning_style: str


class UserScopedRequest(BaseModel):
    user_id: str


@router.post("/onboarding/start")
async def start_onboarding(req: OnboardingStartRequest):
    result = validate_exam_id(req.exam_name)
    if not result.accepted:
        return {"accepted": False, "message": result.message}

    exam_id = result.exam_id
    canonical_name = result.canonical_name

    onboarding_id = await create_onboarding_run(
        user_id=req.user_id,
        exam_id=exam_id,
        exam_name=canonical_name,
        learning_style=req.learning_style,
    )
    if not onboarding_id:
        raise HTTPException(status_code=503, detail="Onboarding persistence is unavailable")

    await add_feed_event(
        onboarding_id,
        "Onboarding Agent",
        "complete",
        f"{canonical_name} captured. Dispatching the build crew.",
    )
    return {
        "accepted": True,
        "onboarding_id": onboarding_id,
        "exam_id": exam_id,
        "exam_name": canonical_name,
        "step": "agent_feed",
    }


@router.post("/onboarding/state")
async def onboarding_state(req: UserScopedRequest):
    run = await get_latest_onboarding(req.user_id)
    curriculum = await get_active_curriculum(req.user_id, DEFAULT_EXAM_ID)
    return {
        "has_onboarding": bool(run),
        "run": run,
        "curriculum": curriculum,
    }


@router.get("/onboarding/{onboarding_id}/feed")
async def onboarding_feed(onboarding_id: str):
    run = await get_onboarding_run(onboarding_id)
    if not run:
        raise HTTPException(status_code=404, detail="Onboarding run not found")

    async def sse_generator():
        last_id = 0
        while True:
            events = await list_feed_events(onboarding_id, after_id=last_id)
            for event in events:
                last_id = event["id"]
                yield f"data: {json.dumps(event)}\n\n"

            latest = await get_onboarding_run(onboarding_id)
            if latest and latest["status"] in {"complete", "failed"} and not events:
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
