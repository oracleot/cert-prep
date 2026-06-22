from __future__ import annotations

import json
import uuid
from typing import cast

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.runnables import RunnableConfig

from answer_intent import KNOWLEDGE_GAP_ANSWER, normalize_answer_intent
from feedback_repository import feedback_by_cycle
from graphs.session import get_session_graph
from llm import llm_runtime
from onboarding_repository import get_latest_onboarding
from routes.session_models import SessionNextRequest, SessionStartRequest, SessionStateRequest, SessionSubmitRequest
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
    nodes = set(snapshot.next or [])
    if not nodes:
        return "summary"
    return "sage_done" if "rex_rechallenge" in nodes else "ready"


def _clamp_cycles(v: int) -> int:
    return min(5, max(1, v))


@router.post("/session/start")
async def start_session(req: SessionStartRequest):
    graph = get_session_graph()
    thread_id = str(uuid.uuid4())
    config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})
    latest = await get_latest_onboarding(req.user_id) if not req.exam_id else None
    exam_id = req.exam_id or (latest["exam_id"] if latest else "dva-c02")
    state = initial_state(
        user_id=req.user_id, exam_id=exam_id, local_timezone=req.timezone,
        max_cycles=_clamp_cycles(req.max_cycles),
        learning_style=req.learning_style, focus_domain=req.focus_domain,
    )
    state["openrouter_api_key"] = req.openrouter_api_key

    try:
        with llm_runtime(req.openrouter_api_key, req.model_overrides):
            await graph.ainvoke(state, config=config)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    snap = await graph.aget_state(config)
    return {"thread_id": thread_id, "exam_id": snap.values.get("exam_id"),
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
    upd = {"user_answer": user_answer, "answer_intent": answer_intent}
    if req.openrouter_api_key:
        upd["openrouter_api_key"] = req.openrouter_api_key
    await graph.aupdate_state(config, upd)

    async def sse():
        try:
            with llm_runtime(req.openrouter_api_key, req.model_overrides):
                async for event in graph.astream_events(None, config=config, version="v2"):
                    kind, name = event["event"], event["name"]
                    if kind == "on_chat_model_stream":
                        node = event.get("metadata", {}).get("langgraph_node")
                        if node in {"sage_depth", "sage_explain"}:
                            chunk = event["data"].get("chunk")
                            if chunk and hasattr(chunk, "content") and chunk.content:
                                yield f"data: {json.dumps({'type': 'token', 'token': chunk.content})}\n\n"
                    elif kind == "on_chain_end" and name == "evaluate_answer":
                        out = event["data"].get("output")
                        if out and "last_evaluation" in out:
                            yield f"data: {json.dumps({'type': 'evaluation', 'data': json.dumps(out['last_evaluation'])})}\n\n"
                    elif kind == "on_chain_end" and name in {"sage_depth", "sage_explain"}:
                        out = event["data"].get("output") or {}
                        h = out.get("session_history") or []
                        if h:
                            yield f"data: {json.dumps({'type': 'citations', 'data': h[-1].get('citations', [])})}\n\n"
                    elif kind == "on_chain_end" and name == "LangGraph":
                        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': {'message': str(e)}})}\n\n"

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

    return {"thread_id": req.thread_id, "exam_id": snap.values.get("exam_id"),
            "phase": _snapshot_phase(snap), "cycle": snap.values.get("cycle") or 1,
            "max_cycles": snap.values.get("max_cycles") or 2,
            "challenge": snap.values.get("current_challenge") or None,
            "user_answer": snap.values.get("user_answer") or "",
            "answer_intent": snap.values.get("answer_intent") or "attempt",
            "evaluation": evaluation,
            "sage_text": last.get("sage_response", "") if last else "",
            "sage_citations": last.get("citations", []) if last else [],
            "sage_feedback": latest_fb, "results": _session_results(history, feedback)}


@router.post("/session/next")
async def next_challenge(req: SessionNextRequest):
    graph = get_session_graph()
    config = cast(RunnableConfig, {"configurable": {"thread_id": req.thread_id}})
    snap = await graph.aget_state(config)
    if not snap or not snap.values:
        raise HTTPException(status_code=404, detail="Session not found")

    if req.openrouter_api_key:
        await graph.aupdate_state(config, {"openrouter_api_key": req.openrouter_api_key})

    try:
        with llm_runtime(req.openrouter_api_key, req.model_overrides):
            await graph.ainvoke(None, config=config)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    snap = await graph.aget_state(config)
    return {"challenge": snap.values.get("current_challenge"), "cycle": snap.values.get("cycle")}
