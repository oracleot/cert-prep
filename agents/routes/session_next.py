"""Phase 11 — ``POST /session/next`` route.

Extracted from ``routes/session.py`` so the main session route file stays
under the 200-line hard rule. The endpoint resumes the session graph and
generates the next challenge; Phase 11 also re-seeds the prompt's
``response_mode`` via the app-controlled 60/40 mix before invoking.
"""
from __future__ import annotations

from typing import cast

from fastapi import APIRouter, HTTPException
from langchain_core.runnables import RunnableConfig

from graphs.session import get_session_graph
from llm import llm_runtime
from routes.session_mode_mix import pick_response_mode
from routes.session_models import SessionNextRequest

router = APIRouter()


@router.post("/session/next")
async def next_challenge(req: SessionNextRequest):
    graph = get_session_graph()
    config = cast(RunnableConfig, {"configurable": {"thread_id": req.thread_id}})
    snap = await graph.aget_state(config)
    if not snap or not snap.values:
        raise HTTPException(status_code=404, detail="Session not found")
    # Phase 11 — seed the next prompt's response_mode (thread_id = seed).
    next_cycle = snap.values.get("cycle", 1) or 1
    upd: dict = {
        "openrouter_api_key": req.openrouter_api_key,
        "current_response_mode": pick_response_mode(next_cycle, req.thread_id),
    }
    upd = {k: v for k, v in upd.items() if v}
    await graph.aupdate_state(config, upd)
    try:
        with llm_runtime(req.openrouter_api_key, req.model_overrides):
            await graph.ainvoke(None, config=config)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    snap = await graph.aget_state(config)
    return {"challenge": snap.values.get("current_challenge"), "cycle": snap.values.get("cycle")}


__all__ = ["router"]
