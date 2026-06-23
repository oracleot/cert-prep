# evaluate_answer node — strict LLM evaluation of a user's answer.
# Phase 1 logic ported from app/api/evaluate/route.ts.

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from answer_intent import normalize_answer_intent
from llm import get_llm, model_for
from prompts.evaluator import MODEL, EvaluatorInput, build_evaluator_prompt
from state import AppState


def _strip_code_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\n?|```$", "", text, flags=re.MULTILINE).strip()


def _coerce_miss_list(value: Any) -> list[str]:
    """Defensive: the evaluator is required to return a JSON list, but if the
    LLM ever returns a string/null/dict we coerce without crashing."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str):
        # Split bullet/numbered lists the LLM sometimes writes instead of JSON.
        items = re.split(r"\n\s*[-*\d\.]+\s*", value)
        return [item.strip().strip('"') for item in items if item.strip()]
    return []


def evaluate_answer(state: AppState, config: RunnableConfig) -> dict:
    """Evaluate the user's answer against the current challenge.

    Phase 9.4 — the prompt now ships ``expected_answer_criteria`` and
    ``traps`` from the concept packet, and the parsed response must include
    ``missed_criteria`` and ``triggered_traps`` lists (empty when nothing
    applies). These flow into ``last_evaluation`` and onward into the
    exchange record for internal concept-miss auditing.
    """
    user_answer = state.get("user_answer") or ""
    if not user_answer:
        # Empty answer (also covers tests that don't seed user_answer).
        # Treat as knowledge_gap so the cycle can still complete with a
        # structured last_evaluation record for downstream nodes.
        return {
            "last_evaluation": {
                "outcome": "incorrect",
                "reasoning": "Knowledge gap: no answer provided.",
                "answer_intent": "knowledge_gap",
                "missed_criteria": [],
                "triggered_traps": [],
            },
            "answer_intent": "knowledge_gap",
        }

    answer_intent = normalize_answer_intent(user_answer, state.get("answer_intent", "attempt"))
    if answer_intent == "knowledge_gap":
        return {
            "last_evaluation": {
                "outcome": "incorrect",
                "reasoning": "Knowledge gap: user indicated they do not know yet.",
                "answer_intent": "knowledge_gap",
                "missed_criteria": [],
                "triggered_traps": [],
            },
            "answer_intent": "knowledge_gap",
        }

    challenge = state["current_challenge"]

    ev_input = EvaluatorInput(
        exam_id=state["exam_id"],
        domain=challenge["domain"],
        topic=challenge["topic"],
        scenario=challenge["scenario"],
        question=challenge["question"],
        user_answer=user_answer,
        expected_answer_criteria=challenge.get("expected_answer_criteria", "") or "",
        traps=list(challenge.get("traps", []) or []),
    )
    system, user = build_evaluator_prompt(ev_input)

    llm = get_llm(model_for("evaluator", MODEL))
    response = llm.invoke(
        [SystemMessage(content=system), HumanMessage(content=user)],
        temperature=0.2,
        max_tokens=320,
    )

    raw = response.content if isinstance(response.content, str) else str(response.content)
    result = json.loads(_strip_code_fences(raw))

    if result.get("outcome") not in ("correct", "incorrect"):
        raise ValueError(f"Evaluator returned invalid outcome: {result}")

    return {
        "last_evaluation": {
            "outcome": result["outcome"],
            "reasoning": result["reasoning"],
            "answer_intent": "attempt",
            # Phase 9.4 — internal miss audit fields, parsed from the LLM JSON.
            "missed_criteria": _coerce_miss_list(result.get("missed_criteria")),
            "triggered_traps": _coerce_miss_list(result.get("triggered_traps")),
        },
        "answer_intent": "attempt",
    }
