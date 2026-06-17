# Application route: list past sessions and load a session's exchanges.
# Reads from the existing `sessions` and `exchanges` tables - no schema change.

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db import get_pool, has_pool

router = APIRouter()

MAX_LIST_LIMIT = 100
DEFAULT_LIST_LIMIT = 50


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
        "COUNT(e.id) AS total_cycles, "
        "COALESCE(SUM(CASE WHEN e.outcome = 'correct' THEN 1 ELSE 0 END), 0) AS correct_count "
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

            await cur.execute(
                "SELECT cycle, domain, topic, challenge, user_answer, outcome, "
                "sage_response, citations FROM exchanges "
                "WHERE session_id = %s ORDER BY cycle",
                (req.session_id,),
            )
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
                "sage_response": e[6],
                "citations": e[7] or [],
            }
            for e in exchange_rows
        ],
    }
