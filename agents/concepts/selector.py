# Closed-book concept selection — task 9.3.
# App code selects the concept before Rex runs; Rex receives only the
# selected concept packet. No freeform topic generation.

from __future__ import annotations

import random
from typing import Any

from .loader import filter_ready, load_all_concepts


class NoReadyConcept(Exception):
    """Raised when no ready concept exists for the requested domain/exam."""

    def __init__(self, exam_id: str = "", domain: str | None = None):
        self.exam_id = exam_id
        self.domain = domain
        parts = [f"exam={exam_id}"] if exam_id else []
        parts.append(f"domain={domain or '*'}")
        super().__init__(f"No ready concept for {', '.join(parts)}")


def select_initial_concept(exam_id: str, domain: str | None = None) -> dict[str, Any]:
    """Return a random ready concept for the exam (optionally scoped to domain).

    Raises NoReadyConcept if no ready concept exists (including unknown exam).
    """
    try:
        all_concepts = load_all_concepts(exam_id)
    except FileNotFoundError:
        raise NoReadyConcept(exam_id=exam_id, domain=domain)
    candidates = filter_ready(all_concepts, domain=domain) if domain else all_concepts
    if not candidates:
        raise NoReadyConcept(exam_id=exam_id, domain=domain)
    return random.choice(candidates)


def _prioritise_concepts(
    candidates: list[dict[str, Any]],
    history_by_concept: dict[str, str],
    previous_concept_id: str,
) -> dict[str, Any]:
    """Apply weak > uncovered > any priority and return the selected concept.

    Raises NoReadyConcept if no qualifying concept remains.
    """
    # Priority 1: weak (prior incorrect).
    weak = [c for c in candidates if history_by_concept.get(c["id"]) == "incorrect"]
    if weak:
        return random.choice(weak)

    # Priority 2: uncovered (no prior exchange) — exclude previous_concept_id.
    uncovered = [
        c for c in candidates
        if c["id"] not in history_by_concept and c["id"] != previous_concept_id
    ]
    if uncovered:
        return uncovered[0]  # deterministic: first uncovered in file order

    # Priority 3: any ready concept — exclude previous.
    others = [c for c in candidates if c["id"] != previous_concept_id]
    if not others:
        raise NoReadyConcept(domain=None)
    return random.choice(others)


def select_rechallenge_concept(
    exam_id: str,
    domain: str,
    previous_concept_id: str,
    history: list[dict[str, Any]],
    concept_id: str = "",
) -> dict[str, Any]:
    """Return a ready concept in the same domain, excluding the previous one.

    Priority: weak (prior incorrect) > uncovered (no prior exchange) > any.
    Falls back to any ready same-domain concept if no weak or uncovered exist.
    Raises NoReadyConcept if zero ready same-domain concepts remain.
    """
    all_concepts = load_all_concepts(exam_id)
    candidates = filter_ready(all_concepts, domain=domain)
    if not candidates:
        raise NoReadyConcept(exam_id=exam_id, domain=domain)

    history_by_concept: dict[str, str] = {
        row["concept_id"]: row["outcome"]
        for row in history
        if row["concept_id"] is not None
    }
    return _prioritise_concepts(candidates, history_by_concept, previous_concept_id)
