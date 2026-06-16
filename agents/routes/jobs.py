from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from blueprint_scout import BlueprintScoutResult, resolve_blueprint
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


def _weights_summary(domains: list[dict]) -> str:
    return ", ".join(f"{d['name']} {d['weight']}%" for d in domains)


async def _require_blueprint(exam_id: str) -> BlueprintScoutResult:
    result = await resolve_blueprint(exam_id)
    if result.accepted:
        return result
    raise HTTPException(status_code=422, detail=result.message)


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
            f"Resolving {exam_id.upper()} against the official-source allowlist.",
        )
        result = await _require_blueprint(exam_id)
        blueprint = result.domains
        await save_blueprint(req.onboarding_id, blueprint)
        await add_feed_event(
            req.onboarding_id,
            "Blueprint Scout",
            "complete",
            f"{result.message} Domains: {_weights_summary(blueprint)}.",
        )
        return {"ok": True, "blueprint": blueprint, "source": result.source}
    except HTTPException as exc:
        await add_feed_event(req.onboarding_id, "Blueprint Scout", "failed", str(exc.detail))
        await fail_onboarding(req.onboarding_id, "Blueprint Scout rejected this exam.")
        raise
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
        if run.get("blueprint"):
            blueprint = run["blueprint"]
        else:
            result = await _require_blueprint(exam_id)
            blueprint = result.domains
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
    except HTTPException as exc:
        await add_feed_event(req.onboarding_id, "Curriculum Builder", "failed", str(exc.detail))
        await fail_onboarding(req.onboarding_id, "Curriculum Builder rejected this exam.")
        raise
    except Exception as exc:
        await fail_onboarding(req.onboarding_id, "Curriculum Builder could not finish.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
