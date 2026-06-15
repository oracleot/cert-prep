# sage_respond node — generates Sage's response (depth on correct, explain on incorrect).
# Phase 1 logic ported from app/api/sage/route.ts.
#
# In the graph, this is split into two nodes: `sage_depth` and `sage_explain`.
# They share `_generate_sage_response`; routing is done by a conditional edge
# after `evaluate_answer`. Both nodes then converge to the cycle-end decision.

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from llm import get_llm
from prompts.sage import MODEL, SageInput, build_sage_depth_prompt, build_sage_explain_prompt
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


def sage_depth(state: AppState) -> dict:
    """Sage adds depth beyond a correct answer."""
    sage_text = _generate_sage_response(state, "depth")
    return _build_cycle_exchange(state, sage_text)


def sage_explain(state: AppState) -> dict:
    """Sage corrects the misconception behind an incorrect answer."""
    sage_text = _generate_sage_response(state, "explain")
    return _build_cycle_exchange(state, sage_text)


def _build_cycle_exchange(state: AppState, sage_text: str) -> dict:
    """Append a completed cycle to session_history (Annotated[list, operator.add])."""
    exchange = {
        "cycle": state.get("cycle", 1),
        "domain": state["current_challenge"]["domain"],
        "topic": state["current_challenge"]["topic"],
        "challenge": state["current_challenge"],
        "user_answer": state["user_answer"],
        "outcome": state["last_evaluation"]["outcome"],
        "sage_response": sage_text,
    }
    return {
        "session_history": [exchange],
    }
