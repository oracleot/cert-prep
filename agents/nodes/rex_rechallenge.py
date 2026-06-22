# rex_rechallenge node — generates a harder variant on the same domain.
# Phase 1 logic ported from app/api/rex/rechallenge/route.ts.

from __future__ import annotations

import json
import re
from typing import Any

from fastapi import HTTPException
from langchain_core.messages import HumanMessage, SystemMessage
from llm import get_llm, model_for
from prompts.rex import MODEL, build_rex_rechallenge_prompt
from state import AppState


def _strip_code_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\n?|```$", "", text, flags=re.MULTILINE).strip()


def _gap_followup_difficulty(current: str, learning_style: str) -> str:
    if learning_style == "guided_explanations":
        return "easy"
    if learning_style == "pressure_drills":
        return current or "hard"
    return "medium"


async def rex_rechallenge(state: AppState) -> dict:
    """Generate a harder challenge on the same domain, increment the cycle.

    Raises HTTPException(422) if no ready concept exists for rechallenge.
    """
    from concepts.selector import NoReadyConcept, select_rechallenge_concept

    current = state["current_challenge"]
    if state.get("answer_intent") == "knowledge_gap":
        target: dict[str, Any] = dict(current)
        target["difficulty"] = _gap_followup_difficulty(
            current.get("difficulty", "medium"), state.get("learning_style", "")
        )
    else:
        try:
            target = await select_rechallenge_concept(
                exam_id=state["exam_id"],
                domain=state["current_domain"],
                previous_concept_id=state.get("current_concept_id", ""),
                user_id=state["user_id"],
            )
        except NoReadyConcept as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    system, user = build_rex_rechallenge_prompt(
        exam_id=state["exam_id"],
        domain=state["current_domain"],
        previous_topic=current["topic"],
        topic=target.get("topic", ""),
        difficulty=target.get("difficulty", "hard"),
        task_statement=target.get("task_statement", ""),
        services=target.get("services", []),
        source_ids=target.get("source_ids", []),
        learning_style=state.get("learning_style", ""),
        familiarity_level=target.get("familiarity_level", state.get("familiarity_level", "new")),
    )

    llm = get_llm(model_for("rex", MODEL))
    response = llm.invoke(
        [SystemMessage(content=system), HumanMessage(content=user)],
        temperature=0.8,
        max_tokens=512,
    )

    raw = response.content if isinstance(response.content, str) else str(response.content)
    challenge = json.loads(_strip_code_fences(raw))

    if not all(k in challenge for k in ("domain", "topic", "scenario", "question")):
        raise ValueError(f"rex_rechallenge returned invalid shape: {challenge}")

    return {
        "current_concept_id": target.get("id", state.get("current_concept_id", "")),
        "current_challenge": {
            "concept_id": target.get("id", state.get("current_concept_id", "")),
            "domain": state["current_domain"],
            "topic": target.get("topic") or challenge["topic"],
            "topic_id": target.get("topic_id", ""),
            "task_statement_id": target.get("task_statement_id", ""),
            "task_statement": target.get("task_statement", ""),
            "difficulty": target.get("difficulty", "hard"),
            "services": target.get("services", []),
            "source_ids": target.get("source_ids", []),
            "familiarity_level": target.get("familiarity_level", state.get("familiarity_level", "new")),
            "scenario": challenge["scenario"],
            "question": challenge["question"],
        },
        "current_topic": target.get("topic") or challenge["topic"],
        "current_topic_id": target.get("topic_id", ""),
        "current_task_statement_id": target.get("task_statement_id", ""),
        "current_task_statement": target.get("task_statement", ""),
        "current_services": target.get("services", []),
        "current_source_ids": target.get("source_ids", []),
        "familiarity_level": target.get("familiarity_level", state.get("familiarity_level", "new")),
        "rex_difficulty": target.get("difficulty", "hard"),
        "answer_intent": "attempt",
        "cycle": state.get("cycle", 1) + 1,
    }
