# evaluate_answer node — strict evaluation of a user's answer.
# Phase 1 logic ported from app/api/evaluate/route.ts.
#
# Phase 11 — option-based challenges take a deterministic exact-match path:
# the LLM evaluator is bypassed and verdict labels (chosen / correct /
# missed / incorrect) are computed in-process from the challenge's
# answer_key. Free-text challenges (legacy) and knowledge-gap submissions
# still flow through the LLM evaluator / knowledge-gap branch.
#
# The option-verdict helpers live in ``option_verdict.py`` to keep this file
# under the 200-line hard rule.

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from answer_intent import normalize_answer_intent
from llm import get_llm, model_for
from nodes.option_verdict import (
    challenge_is_option_based,
    compute_option_verdict,
    extract_selected_labels,
)
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


def _knowledge_gap_eval(reasoning: str) -> dict[str, Any]:
    return {
        "last_evaluation": {
            "outcome": "incorrect",
            "reasoning": reasoning,
            "answer_intent": "knowledge_gap",
            "missed_criteria": [],
            "triggered_traps": [],
            "selected_labels": [],
            "correct_labels": [],
            "missed_labels": [],
            "incorrect_labels": [],
        },
        "answer_intent": "knowledge_gap",
    }


def _option_eval(state: AppState) -> dict[str, Any]:
    challenge = state["current_challenge"]
    selected = extract_selected_labels(state)
    verdict = compute_option_verdict(challenge, selected)
    return {
        "last_evaluation": {
            "outcome": verdict["outcome"],
            "reasoning": verdict["reasoning"],
            "answer_intent": "attempt",
            "missed_criteria": [],
            "triggered_traps": [],
            "selected_labels": verdict["selected_labels"],
            "correct_labels": verdict["correct_labels"],
            "missed_labels": verdict["missed_labels"],
            "incorrect_labels": verdict["incorrect_labels"],
        },
        "answer_intent": "attempt",
    }


def _free_text_eval(state: AppState) -> dict[str, Any]:
    challenge = state["current_challenge"]
    user_answer = state.get("user_answer") or ""
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
            "missed_criteria": _coerce_miss_list(result.get("missed_criteria")),
            "triggered_traps": _coerce_miss_list(result.get("triggered_traps")),
            # Phase 11 — option challenges don't use this branch; defaults are
            # empty so the EvaluationResult TypedDict shape stays valid.
            "selected_labels": [],
            "correct_labels": [],
            "missed_labels": [],
            "incorrect_labels": [],
        },
        "answer_intent": "attempt",
    }


def evaluate_answer(state: AppState, config: RunnableConfig) -> dict:
    """Evaluate the user's answer against the current challenge.

    Phase 9.4 — the prompt ships ``expected_answer_criteria`` and
    ``traps`` from the concept packet; the parsed response must include
    ``missed_criteria`` and ``triggered_traps`` lists (empty when nothing
    applies). These flow into ``last_evaluation`` and onward into the
    exchange record for internal concept-miss auditing.

    Phase 11 — option-based challenges short-circuit the LLM evaluator.
    Verdict is exact-match binary; the four label breakdowns are computed
    deterministically so the UI can render them immediately on receipt of
    the ``evaluation`` SSE event.
    """
    challenge = state["current_challenge"]

    if challenge_is_option_based(challenge):
        return _option_eval(state)

    user_answer = state.get("user_answer") or ""
    if not user_answer:
        return _knowledge_gap_eval("Knowledge gap: no answer provided.")

    answer_intent = normalize_answer_intent(user_answer, state.get("answer_intent", "attempt"))
    if answer_intent == "knowledge_gap":
        return _knowledge_gap_eval("Knowledge gap: user indicated they do not know yet.")

    return _free_text_eval(state)