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
) -> tuple[str, list[Citation], list[str], list[str], list[str]]:
    challenge = state["current_challenge"]
    evaluation = state["last_evaluation"]
    # Phase 9.5 — Sage is grounded exclusively to the concept packet. The
    # challenge carries official_docs / skill_builder_links / lab_links
    # selected by coach_open / rex_rechallenge; we forward them so
    # load_sage_grounding will not fall back to service-name docs.
    grounding = load_sage_grounding(
        exam_id=state["exam_id"],
        topic_id=challenge.get("topic_id", ""),
        topic=challenge["topic"],
        services=challenge.get("services", []),
        source_ids=challenge.get("source_ids", []),
        official_docs=challenge.get("official_docs", []),
        skill_builder_links=challenge.get("skill_builder_links", []),
        lab_links=challenge.get("lab_links", []),
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
        official_docs=challenge.get("official_docs", []) or [],
        skill_builder_links=challenge.get("skill_builder_links", []) or [],
        lab_links=challenge.get("lab_links", []) or [],
        # Phase 11 — forward the option context so Sage can refer to options
        # by label + short paraphrase and explicitly name missed/incorrect
        # labels on multi-response misses.
        response_mode=str(challenge.get("response_mode") or ""),
        options=list(challenge.get("options") or []),
        answer_key=list(challenge.get("answer_key") or []),
        selected_labels=list(evaluation.get("selected_labels") or []),
        missed_labels=list(evaluation.get("missed_labels") or []),
        incorrect_labels=list(evaluation.get("incorrect_labels") or []),
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
    return (
        content,
        grounding["citations"],
        list(challenge.get("official_docs", []) or []),
        list(challenge.get("skill_builder_links", []) or []),
        list(challenge.get("lab_links", []) or []),
    )


def _build_exchange(state: AppState, sage_text: str, citations: list[Citation]) -> dict:
    """Assemble the per-cycle exchange record (in-memory, not yet persisted).

    Phase 9.5 / 9.6 — ``missed_criteria`` and ``triggered_traps`` flow through
    from the evaluator's ``last_evaluation`` (internal concept-miss audit) and
    the three packet link lists are persisted alongside the exchange so the
    Review-next block can be reconstructed from the database row alone.

    Phase 11 — option-based prompts persist their mode + options + answer_key
    on the challenge JSONB (already serialized there by rex_challenge) and
    surface the immediate-verdict label breakdowns on a sibling field set.
    Storing these on the exchange keeps the per-cycle UI consistent even
    after a server restart.
    """
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
        # Phase 9.5: packet link metadata persisted with the exchange.
        "official_docs": list(challenge.get("official_docs", []) or []),
        "skill_builder_links": list(challenge.get("skill_builder_links", []) or []),
        "lab_links": list(challenge.get("lab_links", []) or []),
        # Phase 9.6: internal concept-miss audit fields from the evaluator.
        # Read by ``concept_misses_for_user``; not used in readiness math.
        "missed_criteria": list(evaluation.get("missed_criteria", []) or []),
        "triggered_traps": list(evaluation.get("triggered_traps", []) or []),
        # Phase 11 — option verdict snapshots. Persisted on the exchange so
        # history renders can rebuild the chosen/correct/missed/incorrect
        # overlay even when the challenge JSONB was migrated away.
        "response_mode": str(challenge.get("response_mode") or ""),
        "options": list(challenge.get("options") or []),
        "answer_key": list(challenge.get("answer_key") or []),
        "selected_labels": list(evaluation.get("selected_labels") or []),
        "correct_labels": list(evaluation.get("correct_labels") or []),
        "missed_labels": list(evaluation.get("missed_labels") or []),
        "incorrect_labels": list(evaluation.get("incorrect_labels") or []),
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
            missed_criteria=exchange.get("missed_criteria", []),
            triggered_traps=exchange.get("triggered_traps", []),
            official_docs=exchange.get("official_docs", []),
            skill_builder_links=exchange.get("skill_builder_links", []),
            lab_links=exchange.get("lab_links", []),
            response_mode=exchange.get("response_mode", ""),
            options=exchange.get("options", []),
            answer_key=exchange.get("answer_key", []),
            selected_labels=exchange.get("selected_labels", []),
            correct_labels=exchange.get("correct_labels", []),
            missed_labels=exchange.get("missed_labels", []),
            incorrect_labels=exchange.get("incorrect_labels", []),
        )
        await record_rex_result(state["user_id"], state["exam_id"], exchange["outcome"])
    except Exception:
        logger.exception("Failed to persist exchange/Rex record; continuing without DB persistence.")


async def sage_depth(state: AppState, config: RunnableConfig) -> dict:
    """Sage adds depth beyond a correct answer."""
    sage_text, citations, _official, _skill, _lab = await _generate_sage_response(state, "depth", config)
    exchange = _build_exchange(state, sage_text, citations)
    await _persist_exchange_if_db(state, exchange)
    return {"session_history": [exchange]}


async def sage_explain(state: AppState, config: RunnableConfig) -> dict:
    """Sage corrects the misconception behind an incorrect answer."""
    sage_text, citations, _official, _skill, _lab = await _generate_sage_response(state, "explain", config)
    exchange = _build_exchange(state, sage_text, citations)
    await _persist_exchange_if_db(state, exchange)
    return {"session_history": [exchange]}
