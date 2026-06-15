# POST /session/run
# Invokes the SessionSubgraph end-to-end and returns the final state.
#
# 2.3 scope: pre-seeded user answers; no streaming; no interrupts.
# 2.4 scope: Postgres checkpointer; thread_id identifies the session for
#            resume. Re-running with an existing thread_id loads the prior
#            checkpoint state and continues from there.
# 2.6 will add SSE streaming + human-in-the-loop interrupts.

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from graphs.session import get_session_graph
from state import initial_state

router = APIRouter()


class SessionRunRequest(BaseModel):
    user_id: str = "dev-user"
    pending_user_answers: list[str] | None = None
    # Optional: pass an existing thread_id to resume a session from its
    # last checkpoint. Omit to start a new session.
    thread_id: str | None = None


class SessionRunResponse(BaseModel):
    user_id: str
    domain: str
    cycles_completed: int
    correct: int
    exchanges: list[dict]
    # Echoed back so the caller can resume this session later.
    thread_id: str
    # DB session UUID (set when coach_open ran with the DB online).
    db_session_id: str
    # True when this response came from a resumed checkpoint (no re-run).
    resumed: bool


@router.post("/session/run", response_model=SessionRunResponse)
async def run_session(req: SessionRunRequest) -> SessionRunResponse:
    graph = get_session_graph()
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Resume path: caller supplied an existing thread_id. Load the latest
    # checkpoint and return it without replaying the graph.
    if req.thread_id is not None:
        snapshot = await graph.aget_state(config)
        if snapshot is None or not snapshot.values:
            raise HTTPException(
                status_code=404,
                detail=f"thread_id {thread_id} not found",
            )
        return _build_response(snapshot.values, thread_id=thread_id, resumed=True)

    # New session: seed initial state and run end-to-end.
    state = initial_state(user_id=req.user_id)
    if req.pending_user_answers is not None:
        state["pending_user_answers"] = req.pending_user_answers

    try:
        final = await graph.ainvoke(state, config=config)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e

    return _build_response(final, thread_id=thread_id, resumed=False)


def _build_response(state: dict, thread_id: str, *, resumed: bool) -> SessionRunResponse:
    """Shape the final state into the response model."""
    history = state.get("session_history", []) or []
    real_exchanges = [ex for ex in history if ex.get("cycle", -1) > 0]
    correct = sum(1 for ex in real_exchanges if ex.get("outcome") == "correct")
    return SessionRunResponse(
        user_id=state.get("user_id", "dev-user"),
        domain=state.get("current_domain", ""),
        cycles_completed=len(real_exchanges),
        correct=correct,
        exchanges=real_exchanges,
        thread_id=thread_id,
        db_session_id=state.get("db_session_id", ""),
        resumed=resumed,
    )
