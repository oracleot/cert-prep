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
        # Phase 9 — knowledge-gap rechallenge rebuilds target from the current
        # Challenge TypedDict, which omits `facts` (and may be missing any
        # packet field if upstream nodes dropped it). Without this merge,
        # concept_packet_fields clears `packet["facts"]` to [] and the
        # returned `current_concept_facts` overwrites the previously good
        # facts with [], sending Rex an ungrounded rechallenge prompt.
        # Merge state-level packet fields defensively — current_challenge
        # already carries traps / links / criteria, so setdefault keeps them.
        target.setdefault("facts", list(state.get("current_concept_facts", []) or []))
        target.setdefault("traps", list(state.get("current_concept_traps", []) or []))
        target.setdefault(
            "expected_answer_criteria",
            state.get("current_expected_answer_criteria", "") or "",
        )
        target.setdefault(
            "official_docs",
            list(state.get("current_official_docs", []) or []),
        )
        target.setdefault(
            "skill_builder_links",
            list(state.get("current_skill_builder_links", []) or []),
        )
        target.setdefault(
            "lab_links", list(state.get("current_lab_links", []) or [])
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
        facts=packet["facts"],
        traps=packet["traps"],
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

    resolved_difficulty = packet["difficulty"] if packet["difficulty"] != "medium" else target.get("difficulty", "hard")

    return {
        "current_concept_id": concept_id,
        "current_challenge": {
            "concept_id": concept_id,
            "domain": state["current_domain"],
            "topic": packet["topic"],
            "topic_id": packet["topic_id"],
            "task_statement_id": packet["task_statement_id"],
            "task_statement": target.get("task_statement", ""),
            "difficulty": resolved_difficulty,
            "services": packet["services"],
            "source_ids": packet["source_ids"],
            "familiarity_level": packet["familiarity_level"],
            # Phase 9.5: forward the curated packet resources for the next
            # cycle so Sage stays grounded to the rechallenge's concept.
            "official_docs": packet["official_docs"],
            "skill_builder_links": packet["skill_builder_links"],
            "lab_links": packet["lab_links"],
            "expected_answer_criteria": packet["expected_answer_criteria"],
            "traps": packet["traps"],
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
        "rex_difficulty": resolved_difficulty,
        # Phase 9.4 / 9.5: refresh packet-derived fields on state so the next
        # evaluate_answer + sage_respond use the rechallenge's packet.
        "current_concept_facts": packet["facts"],
        "current_concept_traps": packet["traps"],
        "current_expected_answer_criteria": packet["expected_answer_criteria"],
        "current_official_docs": packet["official_docs"],
        "current_skill_builder_links": packet["skill_builder_links"],
        "current_lab_links": packet["lab_links"],
        "answer_intent": "attempt",
        "cycle": state.get("cycle", 1) + 1,
    }
