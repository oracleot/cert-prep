"""Routes for the spaced-review queue.

``POST /review/queue`` returns concepts whose next drill is due, joined
with the on-disk concept records so the FE can render ``topic``/``domain``
labels without a second roundtrip.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from concepts.loader import load_all_concepts
from review_queue_repository import review_queue_for_user

router = APIRouter()


class ReviewQueueRequest(BaseModel):
    user_id: str
    exam_id: str
    limit: int = 10


@router.post("/review/queue")
async def review_queue(req: ReviewQueueRequest) -> dict:
    """Return due concepts for the spaced-review flow.

    Response shape::

        {due: [
            {
                "concept_id": str,
                "topic": str,
                "domain": str,
                "last_outcome": "correct" | "incorrect",
                "days_since_seen": int,
            },
            ...
        ], total_due: int}

    ``total_due`` is the count *after* filtering but *before* truncation to
    ``limit`` — i.e. how many concepts would be due if the FE asked for an
    unbounded page. Empty queue is ``{due: [], total_due: 0}`` with 200.
    Concepts whose ``concept_id`` is unknown / not ``ready=true`` on disk
    are dropped silently — they cannot be drilled anyway.
    """
    rows = await review_queue_for_user(req.user_id, req.exam_id, req.limit)
    total_due = len(rows)

    by_id = {concept["id"]: concept for concept in load_all_concepts(req.exam_id)}
    due = []
    for row in rows[: req.limit]:
        concept = by_id.get(row["concept_id"])
        if concept is None:
            continue
        due.append(
            {
                "concept_id": concept["id"],
                "topic": concept.get("topic", ""),
                "domain": concept.get("domain", ""),
                "last_outcome": row["last_outcome"],
                "days_since_seen": row["days_since_seen"],
            }
        )
    return {"due": due, "total_due": total_due}