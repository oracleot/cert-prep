from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from graphs.session import get_session_graph
from state import initial_state

router = APIRouter()


class SessionStartRequest(BaseModel):
    user_id: str


class SessionSubmitRequest(BaseModel):
    thread_id: str
    user_answer: str


class SessionNextRequest(BaseModel):
    thread_id: str


class SessionStateRequest(BaseModel):
    thread_id: str


def _session_results(history: list[dict]) -> list[dict]:
    return [
        {"cycle": item["cycle"], "topic": item["topic"], "outcome": item["outcome"]}
        for item in history
        if item.get("outcome") in {"correct", "incorrect"}
    ]


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


@router.post("/session/start")
async def start_session(req: SessionStartRequest):
    graph = get_session_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    state = initial_state(user_id=req.user_id)

    # Run graph until first interrupt (evaluate_answer)
    try:
        await graph.ainvoke(state, config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    snapshot = await graph.aget_state(config)
    return {
        "thread_id": thread_id,
        "challenge": snapshot.values.get("current_challenge"),
    }


@router.post("/session/submit")
async def submit_answer(req: SessionSubmitRequest):
    graph = get_session_graph()
    config = {"configurable": {"thread_id": req.thread_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update state with user answer
    await graph.aupdate_state(config, {"user_answer": req.user_answer})

    async def sse_generator():
        try:
            async for event in graph.astream_events(None, config=config, version="v2"):
                kind = event["event"]
                name = event["name"]

                if kind == "on_chat_model_stream":
                    node = event.get("metadata", {}).get("langgraph_node")
                    if node not in {"sage_depth", "sage_explain"}:
                        continue
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        # Make sure to handle newlines properly for SSE
                        content = json.dumps({"type": "token", "token": chunk.content})
                        yield f"data: {content}\n\n"

                elif kind == "on_chain_end" and name == "evaluate_answer":
                    outputs = event["data"].get("output")
                    if outputs and "last_evaluation" in outputs:
                        eval_result = outputs["last_evaluation"]
                        yield f"data: {json.dumps({'type': 'evaluation', 'data': json.dumps(eval_result)})}\n\n"

                elif kind == "on_chain_end" and name == "LangGraph":
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            err_msg = json.dumps({"type": "error", "error": {"message": str(e)}})
            yield f"data: {err_msg}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@router.post("/session/state")
async def session_state(req: SessionStateRequest):
    graph = get_session_graph()
    config = {"configurable": {"thread_id": req.thread_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail="Session not found")

    history = snapshot.values.get("session_history", [])
    latest_exchange = _latest_exchange(history)

    evaluation = snapshot.values.get("last_evaluation") or None
    if evaluation and evaluation.get("outcome") not in {"correct", "incorrect"}:
        evaluation = None

    return {
        "thread_id": req.thread_id,
        "phase": _snapshot_phase(snapshot),
        "cycle": snapshot.values.get("cycle") or 1,
        "max_cycles": snapshot.values.get("max_cycles") or 2,
        "challenge": snapshot.values.get("current_challenge") or None,
        "user_answer": snapshot.values.get("user_answer") or "",
        "evaluation": evaluation,
        "sage_text": latest_exchange.get("sage_response", "") if latest_exchange else "",
        "results": _session_results(history),
    }


@router.post("/session/next")
async def next_challenge(req: SessionNextRequest):
    graph = get_session_graph()
    config = {"configurable": {"thread_id": req.thread_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        await graph.ainvoke(None, config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    snapshot = await graph.aget_state(config)
    return {
        "challenge": snapshot.values.get("current_challenge"),
        "cycle": snapshot.values.get("cycle"),
    }
