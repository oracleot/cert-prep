# Application route: list past sessions and load a session's exchanges.
# Reads from the existing `sessions` and `exchanges` tables.

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db import get_pool, has_pool

router = APIRouter()

MAX_LIST_LIMIT = 100
DEFAULT_LIST_LIMIT = 50
SESSION_DETAIL_SQL = (
    "SELECT e.cycle, e.domain, e.topic, e.challenge, e.user_answer, e.outcome, "
    "e.answer_intent, e.sage_response, e.citations, e.review_status, "
    "f.feedback_type, f.status, f.excludes_metrics FROM exchanges e "
    "LEFT JOIN sage_feedback f ON f.exchange_id = e.id "
    "WHERE e.session_id = %s ORDER BY e.cycle"
)


class HistoryListRequest(BaseModel):
    user_id: str
    exam_id: str | None = None
    limit: int = DEFAULT_LIST_LIMIT


class HistorySessionRequest(BaseModel):
    user_id: str
    session_id: str


def _iso(value) -> str | None:
    return value.isoformat() if value else None


@router.post("/history/list")
async def history_list(req: HistoryListRequest):
    if not has_pool():
        return {"sessions": []}

    limit = max(1, min(req.limit, MAX_LIST_LIMIT))
    pool = get_pool()

    base_sql = (
        "SELECT s.id::text, s.started_at, s.ended_at, s.exam_id, s.domain, s.topic, "
        "COALESCE(SUM(CASE WHEN e.review_status = 'active' THEN 1 ELSE 0 END), 0) AS total_cycles, "
        "COALESCE(SUM(CASE WHEN e.review_status = 'active' AND e.outcome = 'correct' THEN 1 ELSE 0 END), 0) AS correct_count "
        "FROM sessions s LEFT JOIN exchanges e ON e.session_id = s.id "
        "WHERE s.user_id = %s "
    )

    if req.exam_id:
        sql = base_sql + "AND s.exam_id = %s GROUP BY s.id ORDER BY s.started_at DESC LIMIT %s"
        params: tuple = (req.user_id, req.exam_id, limit)
    else:
        sql = base_sql + "GROUP BY s.id ORDER BY s.started_at DESC LIMIT %s"
        params = (req.user_id, limit)

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, params)
            rows = await cur.fetchall()

    return {
        "sessions": [
            {
                "id": row[0],
                "started_at": _iso(row[1]),
                "ended_at": _iso(row[2]),
                "exam_id": row[3],
                "domain": row[4],
                "topic": row[5],
                "total_cycles": int(row[6] or 0),
                "correct_count": int(row[7] or 0),
            }
            for row in rows
        ]
    }


@router.post("/history/session")
async def history_session(req: HistorySessionRequest):
    if not has_pool():
        raise HTTPException(status_code=503, detail="Database not available")

    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id::text, started_at, ended_at, exam_id, domain, topic, user_id "
                "FROM sessions WHERE id = %s",
                (req.session_id,),
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Session not found")
            if row[6] != req.user_id:
                raise HTTPException(status_code=403, detail="Not your session")

            await cur.execute(SESSION_DETAIL_SQL, (req.session_id,))
            exchange_rows = await cur.fetchall()

    return {
        "id": row[0],
        "started_at": _iso(row[1]),
        "ended_at": _iso(row[2]),
        "exam_id": row[3],
        "domain": row[4],
        "topic": row[5],
        "exchanges": [
            {
                "cycle": e[0],
                "domain": e[1],
                "topic": e[2],
                "challenge": e[3],
                "user_answer": e[4],
                "outcome": e[5],
                "answer_intent": e[6] or "attempt",
                "sage_response": e[7],
                "citations": e[8] or [],
                "review_status": e[9],
                "feedback": {
                    "feedback_type": e[10],
                    "status": e[11],
                    "excludes_metrics": bool(e[12]),
                    "review_status": e[9],
                } if e[10] else None,
            }
            for e in exchange_rows
        ],
    }
