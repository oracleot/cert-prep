# rex_rechallenge node — generates a harder variant on the same domain.
# Phase 1 logic ported from app/api/rex/rechallenge/route.ts.

from __future__ import annotations

import json
import re
from typing import Any

from fastapi import HTTPException
from langchain_core.messages import HumanMessage, SystemMessage

from concepts.packet import concept_packet_fields
from concepts.selector import NoReadyConcept, select_rechallenge_concept
from llm import get_llm, llm_runtime, model_for
from prompts.rex import MODEL, build_rex_rechallenge_prompt
from repositories import exchange_history_for_user
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
    current = state["current_challenge"]
    if state.get("answer_intent") == "knowledge_gap":
        target: dict[str, Any] = dict(current)
        target["difficulty"] = _gap_followup_difficulty(
            current.get("difficulty", "medium"), state.get("learning_style", "")
        )
    else:
        history = await exchange_history_for_user(
            state["exam_id"],
            state["user_id"],
        )
        try:
            target = select_rechallenge_concept(
                exam_id=state["exam_id"],
                domain=state["current_domain"],
                previous_concept_id=state.get("current_concept_id", ""),
                history=history,
                concept_id=current.get("concept_id", ""),
            )
        except NoReadyConcept as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    concept_id = target.get("id", target.get("concept_id", state.get("current_concept_id", "")))
    packet = concept_packet_fields({**target, "id": concept_id})

    system, user = build_rex_rechallenge_prompt(
        exam_id=state["exam_id"],
        domain=state["current_domain"],
        concept_id=concept_id,
        previous_topic=current["topic"],
        topic=packet["topic"],
        difficulty=packet["difficulty"] if packet["difficulty"] != "medium" else target.get("difficulty", "hard"),
        task_statement=target.get("task_statement", ""),
        services=packet["services"],
        source_ids=packet["source_ids"],
        learning_style=state.get("learning_style", ""),
        familiarity_level=packet["familiarity_level"],
    )

    # Set the API key in the runtime context so get_llm finds it.
    # llm_runtime uses a ContextVar; nest_asyncio's loop.run() creates a fresh
    # event loop per call, so we set the context var inside this node's own
    # execution rather than relying on cross-loop inheritance.
    api_key = state.get("openrouter_api_key") or ""
    with llm_runtime(api_key):
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
        "current_concept_id": concept_id,
        "current_challenge": {
            "concept_id": concept_id,
            "domain": state["current_domain"],
            "topic": packet["topic"],
            "topic_id": packet["topic_id"],
            "task_statement_id": packet["task_statement_id"],
            "task_statement": target.get("task_statement", ""),
            "difficulty": packet["difficulty"] if packet["difficulty"] != "medium" else target.get("difficulty", "hard"),
            "services": packet["services"],
            "source_ids": packet["source_ids"],
            "familiarity_level": packet["familiarity_level"],
            "scenario": challenge["scenario"],
            "question": challenge["question"],
        },
        "current_topic": packet["topic"],
        "current_topic_id": packet["topic_id"],
        "current_task_statement_id": packet["task_statement_id"],
        "current_task_statement": target.get("task_statement", ""),
        "current_services": packet["services"],
        "current_source_ids": packet["source_ids"],
        "familiarity_level": packet["familiarity_level"],
        "rex_difficulty": packet["difficulty"] if packet["difficulty"] != "medium" else target.get("difficulty", "hard"),
        "answer_intent": "attempt",
        "cycle": state.get("cycle", 1) + 1,
    }
