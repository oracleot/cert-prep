"""Mode-aware state overrides for ``POST /session/start``.

Kept out of ``routes/session.py`` so the route file stays under the 200-line
hard rule. The helper mirrors the field-set emitted by
``nodes/coach_open.py`` so a pinned concept is indistinguishable from one
that ``coach_open`` would have selected itself.
"""
from __future__ import annotations

from typing import Any

from concepts.loader import find_concept
from concepts.packet import concept_packet_fields
from concepts.selector import NoReadyConcept, select_review_concept
from routes.session_models import SessionStartRequest


async def apply_mode_to_state(state: dict[str, Any], req: SessionStartRequest) -> dict[str, Any]:
    """Return state overrides for ``req.mode``.

    ``mode == "new"`` (the default) returns ``{}`` so callers can update
    unconditionally. ``mode == "review"`` returns a dict that pins the
    session to a specific concept — either the one named in
    ``req.concept_id`` or the top pick from ``select_review_concept``.
    """
    if req.mode != "review":
        return {}

    if req.concept_id:
        concept = find_concept(req.exam_id, req.concept_id)
    else:
        concept = await select_review_concept(user_id=req.user_id, exam_id=req.exam_id)

    packet = concept_packet_fields(concept)
    return {
        "current_concept_id": concept["id"],
        "current_domain": concept["domain"],
        "current_topic": packet["topic"],
        "current_topic_id": packet["topic_id"],
        "current_task_statement_id": packet["task_statement_id"],
        "current_task_statement": concept.get("task_statement", ""),
        "current_services": packet["services"],
        "current_source_ids": packet["source_ids"],
        "familiarity_level": packet["familiarity_level"],
        "current_concept_facts": packet["facts"],
        "current_concept_traps": packet["traps"],
        "current_expected_answer_criteria": packet["expected_answer_criteria"],
        "current_official_docs": packet["official_docs"],
        "current_skill_builder_links": packet["skill_builder_links"],
        "current_lab_links": packet["lab_links"],
    }


__all__ = ["apply_mode_to_state", "NoReadyConcept"]