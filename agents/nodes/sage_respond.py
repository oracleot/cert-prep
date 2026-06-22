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

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from llm import get_llm, model_for
from performance_repository import record_rex_result
from prompts.sage import MODEL, SageInput, build_sage_depth_prompt, build_sage_explain_prompt
from repositories import create_exchange
from sage_sources import Citation, load_sage_grounding
from state import AppState

logger = logging.getLogger(__name__)


async def _generate_sage_response(
    state: AppState,
    kind: str,
    config: RunnableConfig,
) -> tuple[str, list[Citation]]:
    challenge = state["current_challenge"]
    evaluation = state["last_evaluation"]
    grounding = load_sage_grounding(
        exam_id=state["exam_id"],
        topic_id=challenge.get("topic_id", ""),
        topic=challenge["topic"],
        services=challenge.get("services", []),
        source_ids=challenge.get("source_ids", []),
    )

    sage_input = SageInput(
        domain=challenge["domain"],
        topic=challenge["topic"],
        scenario=challenge["scenario"],
        question=challenge["question"],
        user_answer=state["user_answer"],
        reasoning=evaluation["reasoning"],
        source_context=grounding["source_context"],
        has_verified_sources=bool(grounding["citations"]),
        learning_style=state.get("learning_style", ""),
        answer_intent=state.get("answer_intent", "attempt"),
        familiarity_level=challenge.get("familiarity_level", state.get("familiarity_level", "new")),
    )

    if kind == "depth":
        system, user = build_sage_depth_prompt(sage_input)
    else:
        system, user = build_sage_explain_prompt(sage_input)

    llm = get_llm(model_for("sage", MODEL))
    response = await llm.ainvoke(
        [SystemMessage(content=system), HumanMessage(content=user)],
        config=config,
    )
    content = response.content if isinstance(response.content, str) else str(response.content)
    return content, grounding["citations"]


def _build_exchange(state: AppState, sage_text: str, citations: list[Citation]) -> dict:
    """Assemble the per-cycle exchange record (in-memory, not yet persisted)."""
    challenge = state["current_challenge"]
    evaluation = state["last_evaluation"]
    return {
        "cycle": state.get("cycle", 1),
        "domain": challenge["domain"],
        "topic": challenge["topic"],
        "challenge": challenge,
        "concept_id": challenge.get("concept_id", state.get("current_concept_id", "")),
        "user_answer": state["user_answer"],
        "outcome": evaluation["outcome"],
        "answer_intent": state.get("answer_intent", "attempt"),
        "sage_response": sage_text,
        "citations": citations,
    }


async def _persist_exchange_if_db(state: AppState, exchange: dict) -> None:
    """Write the exchange to Postgres when db_session_id is set (i.e. coach_open
    ran with the DB online). Skipped when empty so the graph stays runnable
    in tests / without a DB."""
    session_id = state.get("db_session_id", "")
    if not session_id:
        return
    try:
        await create_exchange(
            session_id=session_id,
            cycle=exchange["cycle"],
            domain=exchange["domain"],
            topic=exchange["topic"],
            challenge=exchange["challenge"],
            user_answer=exchange["user_answer"],
            outcome=exchange["outcome"],
            answer_intent=exchange.get("answer_intent", "attempt"),
            sage_response=exchange["sage_response"],
            citations=exchange["citations"],
            concept_id=exchange.get("concept_id", ""),
        )
        await record_rex_result(state["user_id"], state["exam_id"], exchange["outcome"])
    except Exception:
        logger.exception("Failed to persist exchange/Rex record; continuing without DB persistence.")


async def sage_depth(state: AppState, config: RunnableConfig) -> dict:
    """Sage adds depth beyond a correct answer."""
    sage_text, citations = await _generate_sage_response(state, "depth", config)
    exchange = _build_exchange(state, sage_text, citations)
    await _persist_exchange_if_db(state, exchange)
    return {"session_history": [exchange]}


async def sage_explain(state: AppState, config: RunnableConfig) -> dict:
    """Sage corrects the misconception behind an incorrect answer."""
    sage_text, citations = await _generate_sage_response(state, "explain", config)
    exchange = _build_exchange(state, sage_text, citations)
    await _persist_exchange_if_db(state, exchange)
    return {"session_history": [exchange]}
