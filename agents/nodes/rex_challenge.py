# rex_challenge node — generates the first challenge for a session.
# Phase 1 logic ported from app/api/rex/challenge/route.ts.

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from llm import get_llm, model_for
from prompts.rex import MODEL, build_rex_challenge_prompt
from state import AppState


def _strip_code_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\n?|```$", "", text, flags=re.MULTILINE).strip()


def rex_challenge(state: AppState, config: RunnableConfig) -> dict:
    """Generate a challenge for the current exam domain + difficulty."""
    system, user = build_rex_challenge_prompt(
        exam_id=state["exam_id"],
        domain=state["current_domain"],
        topic=state.get("current_topic", ""),
        difficulty=state.get("rex_difficulty", "medium"),
        task_statement=state.get("current_task_statement", ""),
        services=state.get("current_services", []),
        source_ids=state.get("current_source_ids", []),
        concept_id=state.get("current_concept_id", ""),
        learning_style=state.get("learning_style", ""),
        familiarity_level=state.get("familiarity_level", "new"),
    )

    llm = get_llm(model_for("rex", MODEL))
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])

    raw = response.content if isinstance(response.content, str) else str(response.content)
    challenge = json.loads(_strip_code_fences(raw))

    if not all(k in challenge for k in ("domain", "topic", "scenario", "question")):
        raise ValueError(f"rex_challenge returned invalid shape: {challenge}")

    return {
        "current_challenge": {
            "concept_id": state.get("current_concept_id", ""),
            "domain": state["current_domain"],
            "topic": state.get("current_topic") or challenge["topic"],
            "topic_id": state.get("current_topic_id", ""),
            "task_statement_id": state.get("current_task_statement_id", ""),
            "task_statement": state.get("current_task_statement", ""),
            "difficulty": state.get("rex_difficulty", "medium"),
            "services": state.get("current_services", []),
            "source_ids": state.get("current_source_ids", []),
            "familiarity_level": state.get("familiarity_level", "new"),
            "scenario": challenge["scenario"],
            "question": challenge["question"],
        },
    }
