# sage_respond node — generates Sage's response (depth on correct, explain on incorrect).
# Phase 1 logic ported from app/api/sage/route.ts.
#
# In the graph, this is split into two nodes: `sage_depth` and `sage_explain`.
# They share `_generate_sage_response`; routing is done by a conditional edge
# after `evaluate_answer`. Both nodes then converge to the cycle-end decision.
#
# 2.4: each completed cycle is also written to the `exchanges` table when
# a `db_session_id` is in state (set by coach_open).

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from llm import get_llm
from prompts.sage import MODEL, SageInput, build_sage_depth_prompt, build_sage_explain_prompt
from repositories import create_exchange
from state import AppState


def _generate_sage_response(state: AppState, kind: str) -> str:
    challenge = state["current_challenge"]
    evaluation = state["last_evaluation"]

    sage_input = SageInput(
        domain=challenge["domain"],
        topic=challenge["topic"],
        scenario=challenge["scenario"],
        question=challenge["question"],
        user_answer=state["user_answer"],
        reasoning=evaluation["reasoning"],
    )

    if kind == "depth":
        system, user = build_sage_depth_prompt(sage_input)
    else:
        system, user = build_sage_explain_prompt(sage_input)

    llm = get_llm(MODEL)
    response = llm.invoke(
        [SystemMessage(content=system), HumanMessage(content=user)],
        temperature=0.7,
        max_tokens=512,
    )
    return response.content if isinstance(response.content, str) else str(response.content)


def _build_exchange(state: AppState, sage_text: str) -> dict:
    """Assemble the per-cycle exchange record (in-memory, not yet persisted)."""
    challenge = state["current_challenge"]
    evaluation = state["last_evaluation"]
    return {
        "cycle": state.get("cycle", 1),
        "domain": challenge["domain"],
        "topic": challenge["topic"],
        "challenge": challenge,
        "user_answer": state["user_answer"],
        "outcome": evaluation["outcome"],
        "sage_response": sage_text,
    }


async def _persist_exchange_if_db(state: AppState, exchange: dict) -> None:
    """Write the exchange to Postgres when db_session_id is set (i.e. coach_open
    ran with the DB online). Skipped when empty so the graph stays runnable
    in tests / without a DB."""
    session_id = state.get("db_session_id", "")
    if not session_id:
        return
    await create_exchange(
        session_id=session_id,
        cycle=exchange["cycle"],
        domain=exchange["domain"],
        topic=exchange["topic"],
        challenge=exchange["challenge"],
        user_answer=exchange["user_answer"],
        outcome=exchange["outcome"],
        sage_response=exchange["sage_response"],
    )


async def sage_depth(state: AppState) -> dict:
    """Sage adds depth beyond a correct answer."""
    sage_text = _generate_sage_response(state, "depth")
    exchange = _build_exchange(state, sage_text)
    await _persist_exchange_if_db(state, exchange)
    return {"session_history": [exchange]}


async def sage_explain(state: AppState) -> dict:
    """Sage corrects the misconception behind an incorrect answer."""
    sage_text = _generate_sage_response(state, "explain")
    exchange = _build_exchange(state, sage_text)
    await _persist_exchange_if_db(state, exchange)
    return {"session_history": [exchange]}
