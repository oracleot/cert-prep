# rex_rechallenge node — generates a harder variant on the same domain.
# Phase 1 logic ported from app/api/rex/rechallenge/route.ts.

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from curriculum_repository import choose_rechallenge_target
from llm import get_llm
from prompts.rex import MODEL, build_rex_rechallenge_prompt
from state import AppState


def _strip_code_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\n?|```$", "", text, flags=re.MULTILINE).strip()


async def rex_rechallenge(state: AppState) -> dict:
    """Generate a harder challenge on the same domain, increment the cycle."""
    target = await choose_rechallenge_target(
        user_id=state["user_id"],
        exam_id=state.get("exam_id", "dva-c02"),
        domain=state["current_domain"],
        previous_topic=state["current_challenge"]["topic"],
        previous_task_statement_id=state["current_challenge"].get("task_statement_id", ""),
    )
    system, user = build_rex_rechallenge_prompt(
        exam_id=state.get("exam_id", "dva-c02"),
        domain=state["current_domain"],
        previous_topic=state["current_challenge"]["topic"],
        topic=target.get("topic", ""),
        difficulty=target.get("difficulty", "hard"),
        task_statement=target.get("task_statement", ""),
        services=target.get("services", []),
        source_ids=target.get("source_ids", []),
    )

    llm = get_llm(MODEL)
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
        "current_challenge": {
            "domain": state["current_domain"],
            "topic": target.get("topic") or challenge["topic"],
            "topic_id": target.get("topic_id", ""),
            "task_statement_id": target.get("task_statement_id", ""),
            "task_statement": target.get("task_statement", ""),
            "difficulty": target.get("difficulty", "hard"),
            "services": target.get("services", []),
            "source_ids": target.get("source_ids", []),
            "scenario": challenge["scenario"],
            "question": challenge["question"],
        },
        "current_topic": target.get("topic") or challenge["topic"],
        "current_topic_id": target.get("topic_id", ""),
        "current_task_statement_id": target.get("task_statement_id", ""),
        "current_task_statement": target.get("task_statement", ""),
        "current_services": target.get("services", []),
        "current_source_ids": target.get("source_ids", []),
        "rex_difficulty": target.get("difficulty", "hard"),
        "cycle": state.get("cycle", 1) + 1,
    }
