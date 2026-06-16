from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from blueprint import default_blueprint
from curriculum_repository import build_curriculum, create_curriculum
from exam_artifacts import load_artifact_from_file
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


def _blueprint_for(exam_id: str) -> list[dict]:
    """Load the artifact's domain list. Falls back to the sync shim on miss."""
    try:
        artifact = load_artifact_from_file(exam_id)
        return artifact.get("domains", [])
    except FileNotFoundError:
        return default_blueprint()


def _weights_summary(domains: list[dict]) -> str:
    return ", ".join(f"{d['name']} {d['weight']}%" for d in domains)


@router.post("/jobs/blueprint-scout")
async def run_blueprint_scout(req: JobRequest):
    run = await get_onboarding_run(req.onboarding_id)
    if not run:
        raise HTTPException(status_code=404, detail="Onboarding run not found")

    try:
        exam_id = run["exam_id"]
        await update_run_status(req.onboarding_id, "blueprint_running", "agent_feed")
        await add_feed_event(
            req.onboarding_id,
            "Blueprint Scout",
            "running",
            f"Reading the {exam_id.upper()} blueprint and carving it into exam domains.",
        )
        blueprint = _blueprint_for(exam_id)
        await save_blueprint(req.onboarding_id, blueprint)
        await add_feed_event(
            req.onboarding_id,
            "Blueprint Scout",
            "complete",
            f"Blueprint locked: {_weights_summary(blueprint)}.",
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
        exam_id = run["exam_id"]
        blueprint = run.get("blueprint") or _blueprint_for(exam_id)
        domains = build_curriculum(blueprint, run["learning_style"])
        curriculum_id = await create_curriculum(
            user_id=run["user_id"],
            exam_id=exam_id,
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
