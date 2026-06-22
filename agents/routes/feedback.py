from __future__ import annotations

from typing import cast

from fastapi import APIRouter, HTTPException
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from feedback_repository import create_sage_feedback
from graphs.session import get_session_graph

router = APIRouter()


class SageFeedbackRequest(BaseModel):
    thread_id: str
    cycle: int
    feedback_type: str
    comment: str


@router.post("/session/feedback")
async def sage_feedback(req: SageFeedbackRequest):
    graph = get_session_graph()
    config = cast(RunnableConfig, {"configurable": {"thread_id": req.thread_id}})
    snapshot = await graph.aget_state(config)
    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail="Session not found")

    session_id = snapshot.values.get("db_session_id")
    if not session_id:
        raise HTTPException(status_code=503, detail="Session persistence is unavailable")

    try:
        feedback = await create_sage_feedback(
            thread_id=req.thread_id,
            session_id=session_id,
            cycle=req.cycle,
            feedback_type=req.feedback_type,
            comment=req.comment,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    return {"feedback": feedback}
