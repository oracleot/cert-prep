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
    results = []
    for item in history:
        if item.get("outcome") not in {"correct", "incorrect"}:
            continue
        result = {"cycle": item["cycle"], "topic": item["topic"], "outcome": item["outcome"], "answer_intent": item.get("answer_intent", "attempt")}
        if item["cycle"] in feedback:
            result["feedback"] = feedback[item["cycle"]]
            result["review_status"] = feedback[item["cycle"]]["review_status"]
        results.append(result)
    return results


def _latest_exchange(history: list[dict]) -> dict | None:
    for item in reversed(history):
        if item.get("outcome") in {"correct", "incorrect"}:
            return item
    return None


def _snapshot_phase(snapshot) -> str:
    next_nodes = set(snapshot.next or [])
    if not next_nodes:
        return "summary"
    if "rex_rechallenge" in next_nodes:
        return "sage_done"
    return "ready"


def _clamp_cycles(value: int) -> int:
    return min(5, max(1, value))


@router.post("/session/start")
async def start_session(req: SessionStartRequest):
    graph = get_session_graph()
    thread_id = str(uuid.uuid4())
    config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})
    latest = await get_latest_onboarding(req.user_id) if not req.exam_id else None
    exam_id = req.exam_id or (latest["exam_id"] if latest else "dva-c02")
    state = initial_state(
        user_id=req.user_id,
        exam_id=exam_id,
        local_timezone=req.timezone,
        max_cycles=_clamp_cycles(req.max_cycles),
        learning_style=req.learning_style,
        focus_domain=req.focus_domain,
    )

    try:
        with llm_runtime(req.openrouter_api_key, req.model_overrides):
            await graph.ainvoke(state, config=config)
    except HTTPException:
        raise  # Let FastAPI handle HTTPExceptions (e.g. 422 from NoReadyConcept)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    snapshot = await graph.aget_state(config)
    return {
        "thread_id": thread_id,
        "exam_id": snapshot.values.get("exam_id"),
        "max_cycles": snapshot.values.get("max_cycles") or 2,
        "challenge": snapshot.values.get("current_challenge"),
    }


@router.post("/session/submit")
async def submit_answer(req: SessionSubmitRequest):
    graph = get_session_graph()
    config = cast(RunnableConfig, {"configurable": {"thread_id": req.thread_id}})

    snapshot = await graph.aget_state(config)
    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail="Session not found")

    answer_intent = normalize_answer_intent(req.user_answer, req.answer_intent)
    user_answer = req.user_answer or (KNOWLEDGE_GAP_ANSWER if answer_intent == "knowledge_gap" else "")
    await graph.aupdate_state(config, {"user_answer": user_answer, "answer_intent": answer_intent})

    async def sse_generator():
        try:
            with llm_runtime(req.openrouter_api_key, req.model_overrides):
                async for event in graph.astream_events(None, config=config, version="v2"):
                    kind = event["event"]
                    name = event["name"]

                    if kind == "on_chat_model_stream":
                        node = event.get("metadata", {}).get("langgraph_node")
                        if node not in {"sage_depth", "sage_explain"}:
                            continue
                        chunk = event["data"].get("chunk")
                        if chunk is not None and hasattr(chunk, "content") and chunk.content:
                            content = json.dumps({"type": "token", "token": chunk.content})
                            yield f"data: {content}\n\n"

                    elif kind == "on_chain_end" and name == "evaluate_answer":
                        outputs = event["data"].get("output")
                        if outputs and "last_evaluation" in outputs:
                            eval_result = outputs["last_evaluation"]
                            yield f"data: {json.dumps({'type': 'evaluation', 'data': json.dumps(eval_result)})}\n\n"

                    elif kind == "on_chain_end" and name in {"sage_depth", "sage_explain"}:
                        outputs = event["data"].get("output") or {}
                        history = outputs.get("session_history") or []
                        if history:
                            citations = history[-1].get("citations", [])
                            yield f"data: {json.dumps({'type': 'citations', 'data': citations})}\n\n"

                    elif kind == "on_chain_end" and name == "LangGraph":
                        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            err_msg = json.dumps({"type": "error", "error": {"message": str(e)}})
            yield f"data: {err_msg}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@router.post("/session/state")
async def session_state(req: SessionStateRequest):
    graph = get_session_graph()
    config = cast(RunnableConfig, {"configurable": {"thread_id": req.thread_id}})

    snapshot = await graph.aget_state(config)
    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail="Session not found")

    history = snapshot.values.get("session_history", [])
    latest_exchange = _latest_exchange(history)
    session_id = snapshot.values.get("db_session_id", "")
    feedback = await feedback_by_cycle(session_id)
    latest_feedback = feedback.get(latest_exchange["cycle"]) if latest_exchange else None

    evaluation = snapshot.values.get("last_evaluation") or None
    if evaluation and evaluation.get("outcome") not in {"correct", "incorrect"}:
        evaluation = None

    return {
        "thread_id": req.thread_id,
        "exam_id": snapshot.values.get("exam_id"),
        "phase": _snapshot_phase(snapshot),
        "cycle": snapshot.values.get("cycle") or 1,
        "max_cycles": snapshot.values.get("max_cycles") or 2,
        "challenge": snapshot.values.get("current_challenge") or None,
        "user_answer": snapshot.values.get("user_answer") or "",
        "answer_intent": snapshot.values.get("answer_intent") or "attempt",
        "evaluation": evaluation,
        "sage_text": latest_exchange.get("sage_response", "") if latest_exchange else "",
        "sage_citations": latest_exchange.get("citations", []) if latest_exchange else [],
        "sage_feedback": latest_feedback,
        "results": _session_results(history, feedback),
    }


@router.post("/session/next")
async def next_challenge(req: SessionNextRequest):
    graph = get_session_graph()
    config = cast(RunnableConfig, {"configurable": {"thread_id": req.thread_id}})

    snapshot = await graph.aget_state(config)
    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        with llm_runtime(req.openrouter_api_key, req.model_overrides):
            await graph.ainvoke(None, config=config)
    except HTTPException:
        raise  # Let FastAPI handle HTTPExceptions (e.g. 422 from NoReadyConcept)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    snapshot = await graph.aget_state(config)
    return {
        "challenge": snapshot.values.get("current_challenge"),
        "cycle": snapshot.values.get("cycle"),
    }
