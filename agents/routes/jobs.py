from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from blueprint import default_blueprint
from curriculum_repository import build_curriculum, create_curriculum
from onboarding_repository import (
    add_feed_event,
    complete_onboarding,
    fail_onboarding,
    get_onboarding_run,
    save_blueprint,
    update_run_status,
)

router = APIRouter()


class JobRequest(BaseModel):
    onboarding_id: str


@router.post("/jobs/blueprint-scout")
async def run_blueprint_scout(req: JobRequest):
    run = await get_onboarding_run(req.onboarding_id)
    if not run:
        raise HTTPException(status_code=404, detail="Onboarding run not found")

    try:
        await update_run_status(req.onboarding_id, "blueprint_running", "agent_feed")
        await add_feed_event(
            req.onboarding_id,
            "Blueprint Scout",
            "running",
            "Reading the DVA-C02 blueprint and carving it into exam domains.",
        )
        blueprint = default_blueprint()
        await save_blueprint(req.onboarding_id, blueprint)
        await add_feed_event(
            req.onboarding_id,
            "Blueprint Scout",
            "complete",
            "Blueprint locked: Deployment 32%, Security 26%, Development 30%, Troubleshooting 12%.",
        )
        return {"ok": True, "blueprint": blueprint}
    except Exception as exc:
        await fail_onboarding(req.onboarding_id, "Blueprint Scout could not finish.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/jobs/curriculum-builder")
async def run_curriculum_builder(req: JobRequest):
    run = await get_onboarding_run(req.onboarding_id)
    if not run:
        raise HTTPException(status_code=404, detail="Onboarding run not found")

    try:
        await update_run_status(req.onboarding_id, "curriculum_running", "agent_feed")
        await add_feed_event(
            req.onboarding_id,
            "Curriculum Builder",
            "running",
            "Sequencing the domains around your selected learning style.",
        )
        blueprint = run.get("blueprint") or default_blueprint()
        domains = build_curriculum(blueprint, run["learning_style"])
        curriculum_id = await create_curriculum(
            user_id=run["user_id"],
            exam_id=run["exam_id"],
            onboarding_id=req.onboarding_id,
            domains=domains,
        )
        await complete_onboarding(req.onboarding_id, curriculum_id)
        await add_feed_event(
            req.onboarding_id,
            "Curriculum Builder",
            "complete",
            "Your first route through the exam is ready.",
        )
        return {"ok": True, "curriculum_id": curriculum_id, "domains": domains}
    except Exception as exc:
        await fail_onboarding(req.onboarding_id, "Curriculum Builder could not finish.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
