# POST /session/run
# Invokes the SessionSubgraph end-to-end and returns the final state.
#
# 2.3 scope: pre-seeded user answers; no streaming; no interrupts.
# 2.6 will add SSE streaming + human-in-the-loop interrupts.

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from graphs.session import session_graph
from state import initial_state

router = APIRouter()


class SessionRunRequest(BaseModel):
    user_id: str = "dev-user"
    pending_user_answers: list[str] | None = None


class SessionRunResponse(BaseModel):
    user_id: str
    domain: str
    cycles_completed: int
    correct: int
    exchanges: list[dict]


@router.post("/session/run", response_model=SessionRunResponse)
async def run_session(req: SessionRunRequest) -> SessionRunResponse:
    state = initial_state(user_id=req.user_id)
    if req.pending_user_answers is not None:
        state["pending_user_answers"] = req.pending_user_answers

    try:
        final = await session_graph.ainvoke(state)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e

    history = final.get("session_history", [])
    real_exchanges = [ex for ex in history if ex.get("cycle", -1) > 0]
    correct = sum(1 for ex in real_exchanges if ex.get("outcome") == "correct")

    return SessionRunResponse(
        user_id=final.get("user_id", req.user_id),
        domain=final.get("current_domain", ""),
        cycles_completed=len(real_exchanges),
        correct=correct,
        exchanges=real_exchanges,
    )
