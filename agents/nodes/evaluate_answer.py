# evaluate_answer node — strict LLM evaluation of a user's answer.
# Phase 1 logic ported from app/api/evaluate/route.ts.

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from llm import get_llm
from prompts.evaluator import MODEL, EvaluatorInput, build_evaluator_prompt
from state import AppState


def _strip_code_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\n?|```$", "", text, flags=re.MULTILINE).strip()


def evaluate_answer(state: AppState) -> dict:
    """Evaluate the user's answer against the current challenge.

    Pop the next pending user answer from state. In 2.3 answers are pre-seeded;
    2.6 will replace this with a LangGraph interrupt that waits for the user.
    """
    pending = list(state.get("pending_user_answers") or [])
    if not pending:
        raise ValueError("No pending user answers in state.")

    user_answer = pending.pop(0)
    challenge = state["current_challenge"]

    ev_input = EvaluatorInput(
        domain=challenge["domain"],
        topic=challenge["topic"],
        scenario=challenge["scenario"],
        question=challenge["question"],
        user_answer=user_answer,
    )
    system, user = build_evaluator_prompt(ev_input)

    llm = get_llm(MODEL)
    response = llm.invoke(
        [SystemMessage(content=system), HumanMessage(content=user)],
        temperature=0.2,
        max_tokens=256,
    )

    raw = response.content if isinstance(response.content, str) else str(response.content)
    result = json.loads(_strip_code_fences(raw))

    if result.get("outcome") not in ("correct", "incorrect"):
        raise ValueError(f"Evaluator returned invalid outcome: {result}")

    return {
        "user_answer": user_answer,
        "last_evaluation": {
            "outcome": result["outcome"],
            "reasoning": result["reasoning"],
        },
        "pending_user_answers": pending,
    }
