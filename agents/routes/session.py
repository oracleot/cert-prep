from __future__ import annotations

import uuid
from typing import cast

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.runnables import RunnableConfig

from answer_intent import KNOWLEDGE_GAP_ANSWER, normalize_answer_intent
from curriculum_repository import get_active_curriculum
from feedback_repository import feedback_by_cycle
from graphs.session import get_session_graph
from llm import llm_runtime
from onboarding_repository import get_latest_onboarding
from option_types import is_response_mode, normalize_option_labels
from routes.session_mode import NoReadyConcept, apply_mode_to_state
from routes.session_mode_mix import pick_response_mode
from routes.session_models import SessionNextRequest, SessionStartRequest, SessionStateRequest, SessionSubmitRequest
from routes.session_submit import submit_sse_generator
from state import initial_state

router = APIRouter()


def _session_results(history: list[dict], feedback: dict[int, dict]) -> list[dict]:
    out = []
    for item in history:
        if item.get("outcome") not in {"correct", "incorrect"}:
            continue
        res = {"cycle": item["cycle"], "topic": item["topic"], "outcome": item["outcome"], "answer_intent": item.get("answer_intent", "attempt")}
        if item["cycle"] in feedback:
            res["feedback"] = feedback[item["cycle"]]
            res["review_status"] = feedback[item["cycle"]]["review_status"]
        out.append(res)
    return out


def _latest_exchange(history: list[dict]) -> dict | None:
    for item in reversed(history):
        if item.get("outcome") in {"correct", "incorrect"}:
            return item
    return None


def _snapshot_phase(snapshot) -> str:
    """Map a LangGraph snapshot to a client ``SessionPhase``.

    The previous implementation collapsed every non-end state to
    ``"ready"``, which dropped the "Sage is streaming, do not let the
    learner advance" lock. Map the next-node set so the client can
    resume a mid-stream session and stay locked until Sage finishes
    (or fails and the client surfaces the error phase).

    Mapping:
      - empty ``next``           → ``"summary"`` (graph at END)
      - ``sage_depth``/``sage_explain`` in ``next`` → ``"streaming_sage"``
        (Sage is currently running; the UI must stay locked)
      - ``rex_rechallenge``/``coach_close`` in ``next`` → ``"sage_done"``
        (Sage finished for the current cycle; waiting on the user)
      - ``rex_challenge``/``coach_open`` in ``next`` → ``"loading_challenge"``
      - ``evaluate_answer`` in ``next`` (paused by interrupt_before)
        → ``"ready"`` (challenge is on screen, waiting for submit)
    """
    nodes = set(snapshot.next or [])
    if not nodes:
        return "summary"
    if "sage_depth" in nodes or "sage_explain" in nodes:
        return "streaming_sage"
    if "rex_rechallenge" in nodes or "coach_close" in nodes:
        return "sage_done"
    if "rex_challenge" in nodes or "coach_open" in nodes:
        return "loading_challenge"
    return "ready"


def _clamp_cycles(v: int) -> int:
    return min(5, max(1, v))


@router.post("/session/start")
async def start_session(req: SessionStartRequest):
    graph = get_session_graph()
    thread_id = str(uuid.uuid4())
    config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})
    latest = await get_latest_onboarding(req.user_id) if not req.exam_id else None
    exam_id = req.exam_id or (latest["exam_id"] if latest else "dva-c02")
    curriculum = await get_active_curriculum(req.user_id, exam_id)
    state = initial_state(
        user_id=req.user_id, exam_id=exam_id, local_timezone=req.timezone,
        max_cycles=_clamp_cycles(req.max_cycles),
        learning_style=req.learning_style, focus_domain=req.focus_domain,
    )
    if curriculum:
        state["curriculum_id"] = curriculum["id"]
    state["openrouter_api_key"] = req.openrouter_api_key
    # Phase 11 — seed the prompt's response_mode via the app-controlled mix.
    # thread_id is the session seed for the 60/40 hash bias.
    state["current_response_mode"] = pick_response_mode(  # type: ignore[typeddict-item]
        state.get("cycle", 1) or 1, thread_id
    )

    try:
        state.update(await apply_mode_to_state(state, req))
    except NoReadyConcept as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        with llm_runtime(req.openrouter_api_key, req.model_overrides):
            await graph.ainvoke(state, config=config)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    snap = await graph.aget_state(config)
    curriculum_id = snap.values.get("curriculum_id") or (curriculum["id"] if curriculum else "")
    return {"thread_id": thread_id, "exam_id": snap.values.get("exam_id"),
            "curriculum_id": curriculum_id,
            "max_cycles": snap.values.get("max_cycles") or 2,
            "challenge": snap.values.get("current_challenge")}


@router.post("/session/submit")
async def submit_answer(req: SessionSubmitRequest):
    graph = get_session_graph()
    config = cast(RunnableConfig, {"configurable": {"thread_id": req.thread_id}})
    snap = await graph.aget_state(config)
    if not snap or not snap.values:
        raise HTTPException(status_code=404, detail="Session not found")

    answer_intent = normalize_answer_intent(req.user_answer, req.answer_intent)
    user_answer = req.user_answer or (KNOWLEDGE_GAP_ANSWER if answer_intent == "knowledge_gap" else "")
    # Phase 11 — forward the learner's selected labels so evaluate_answer can
    # run exact-match on option-based challenges.
    selected_labels = normalize_option_labels(req.selected_labels or [])
    upd: dict = {"user_answer": user_answer, "answer_intent": answer_intent}
    if selected_labels:
        upd["selected_labels"] = selected_labels
    if req.openrouter_api_key:
        upd["openrouter_api_key"] = req.openrouter_api_key
    await graph.aupdate_state(config, upd)

    async def sse():
        async for chunk in submit_sse_generator(
            graph,
            config,
            api_key=req.openrouter_api_key,
            model_overrides=req.model_overrides,
        ):
            yield chunk

    return StreamingResponse(sse(), media_type="text/event-stream")


@router.post("/session/state")
async def session_state(req: SessionStateRequest):
    graph = get_session_graph()
    config = cast(RunnableConfig, {"configurable": {"thread_id": req.thread_id}})
    snap = await graph.aget_state(config)
    if not snap or not snap.values:
        raise HTTPException(status_code=404, detail="Session not found")

    history = snap.values.get("session_history", [])
    last = _latest_exchange(history)
    session_id = snap.values.get("db_session_id", "")
    feedback = await feedback_by_cycle(session_id)
    latest_fb = feedback.get(last["cycle"]) if last else None

    evaluation = snap.values.get("last_evaluation") or None
    if evaluation and evaluation.get("outcome") not in {"correct", "incorrect"}:
        evaluation = None

    challenge = snap.values.get("current_challenge") or None
    if isinstance(challenge, dict):
        # Phase 11 — make sure the challenge payload exposes a response_mode
        # so the client UI doesn't have to guess. Empty mode is fine for
        # legacy / free-text challenges that pre-date the rollout.
        if not is_response_mode(challenge.get("response_mode")):
            challenge = dict(challenge)
            challenge["response_mode"] = challenge.get("response_mode") or ""

    return {"thread_id": req.thread_id, "exam_id": snap.values.get("exam_id"),
            "curriculum_id": snap.values.get("curriculum_id", "") or "",
            "phase": _snapshot_phase(snap), "cycle": snap.values.get("cycle") or 1,
            "max_cycles": snap.values.get("max_cycles") or 2,
            "challenge": challenge,
            "user_answer": snap.values.get("user_answer") or "",
            "answer_intent": snap.values.get("answer_intent") or "attempt",
            "evaluation": evaluation,
            "sage_text": last.get("sage_response", "") if last else "",
            "sage_citations": last.get("citations", []) if last else [],
            "sage_feedback": latest_fb, "results": _session_results(history, feedback)}


# Phase 11 — the /session/next endpoint moved to routes/session_next.py
# so this file stays under the 200-line hard rule.