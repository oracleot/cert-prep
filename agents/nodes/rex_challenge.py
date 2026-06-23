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
    """Generate a challenge for the current exam domain + difficulty.

    Phase 9.4 — Rex is grounded to the concept packet: ``facts`` and ``traps``
    are inlined into the prompt, and the returned ``topic`` is overwritten
    with the packet's topic so a free-roaming LLM cannot drift the challenge
    off-concept.
    """
    packet_topic = state.get("current_topic", "") or ""

    system, user = build_rex_challenge_prompt(
        exam_id=state["exam_id"],
        domain=state["current_domain"],
        topic=packet_topic,
        difficulty=state.get("rex_difficulty", "medium"),
        task_statement=state.get("current_task_statement", ""),
        services=state.get("current_services", []),
        source_ids=state.get("current_source_ids", []),
        concept_id=state.get("current_concept_id", ""),
        learning_style=state.get("learning_style", ""),
        familiarity_level=state.get("familiarity_level", "new"),
        facts=list(state.get("current_concept_facts", []) or []),
        traps=list(state.get("current_concept_traps", []) or []),
    )

    llm = get_llm(model_for("rex", MODEL))
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])

    raw = response.content if isinstance(response.content, str) else str(response.content)
    challenge = json.loads(_strip_code_fences(raw))

    if not all(k in challenge for k in ("domain", "topic", "scenario", "question")):
        raise ValueError(f"rex_challenge returned invalid shape: {challenge}")

    # Enforce packet grounding: if the LLM picked a topic outside the
    # selected concept, snap it back to the packet topic. concept_id is
    # always echoed verbatim so downstream nodes can detect drift.
    resolved_topic = packet_topic or challenge["topic"]

    return {
        "current_challenge": {
            "concept_id": state.get("current_concept_id", ""),
            "domain": state["current_domain"],
            "topic": resolved_topic,
            "topic_id": state.get("current_topic_id", ""),
            "task_statement_id": state.get("current_task_statement_id", ""),
            "task_statement": state.get("current_task_statement", ""),
            "difficulty": state.get("rex_difficulty", "medium"),
            "services": state.get("current_services", []),
            "source_ids": state.get("current_source_ids", []),
            "familiarity_level": state.get("familiarity_level", "new"),
            # Phase 9.5: forward the curated packet resources so Sage (and
            # the persisted exchange record) know which URLs are allowed.
            "official_docs": list(state.get("current_official_docs", []) or []),
            "skill_builder_links": list(state.get("current_skill_builder_links", []) or []),
            "lab_links": list(state.get("current_lab_links", []) or []),
            "expected_answer_criteria": state.get("current_expected_answer_criteria", "") or "",
            "traps": list(state.get("current_concept_traps", []) or []),
            "scenario": challenge["scenario"],
            "question": challenge["question"],
        },
    }
