"""Quality gate for a single concept record.

Every record loaded from YAML must pass the gate before it is used at runtime.
Errors are accumulated so callers can surface all issues at once.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .schema import Concept


@dataclass(frozen=True)
class ConceptValidation:
    """Result of validating a concept record."""

    concept_id: str
    valid: bool
    errors: tuple[str, ...]


_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_AWS_DOCS_RE = re.compile(r"^https?://docs\.aws\.amazon\.com(?:/|$)", re.IGNORECASE)
_VALID_DOMAINS = {"Deployment", "Security", "Development", "Troubleshooting"}


def validate_concept(concept: Concept | dict[str, Any]) -> ConceptValidation:
    """Validate a Concept (or dict equivalent) against the quality gate.

    The gate enforces:
    - Required scalar fields (id, domain, task_statement, lesson_reference, expected_answer_criteria)
    - Stable kebab-case id and known DVA-C02 domain
    - Facts 2–4 inclusive
    - At least 1 trap
    - At least 1 official_docs URL under docs.aws.amazon.com
    - Ready must be bool (default False)

    Returns a ConceptValidation with ``valid=True`` only when all checks pass.
    Errors are accumulated in a tuple so no issue is lost.
    """
    errors: list[str] = []
    concept_id = ""

    if isinstance(concept, dict):
        concept_id = str(concept.get("id", "")).strip()
        errors.extend(_validate_dict(concept))
    else:
        concept_id = concept.id
        errors.extend(_validate_object(concept))

    return ConceptValidation(concept_id=concept_id, valid=len(errors) == 0, errors=tuple(errors))


# ---------------------------------------------------------------------------
# Dict-level validation (raw YAML load before dataclass construction)
# ---------------------------------------------------------------------------


def _validate_dict(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    concept_id = str(data.get("id", ""))
    domain = str(data.get("domain", ""))
    task_statement = str(data.get("task_statement", ""))
    lesson_reference = str(data.get("lesson_reference", ""))
    expected = str(data.get("expected_answer_criteria", ""))
    facts = data.get("facts", [])
    traps = data.get("traps", [])
    official_docs = data.get("official_docs", [])

    # Required scalars
    if not concept_id.strip():
        errors.append("id is required and must be a non-empty string")
    elif not _ID_RE.match(concept_id.strip()):
        errors.append("id must be stable kebab-case")
    if not domain.strip():
        errors.append("domain is required and must be a non-empty string")
    elif domain.strip() not in _VALID_DOMAINS:
        errors.append(f"domain must be one of {sorted(_VALID_DOMAINS)}")
    if not task_statement.strip():
        errors.append("task_statement is required and must be a non-empty string")
    if not lesson_reference.strip():
        errors.append("lesson_reference is required and must be a non-empty string")
    if not expected.strip():
        errors.append("expected_answer_criteria is required and must be a non-empty string")
    if not isinstance(data.get("ready", False), bool):
        errors.append("ready must be a boolean")

    # Facts count
    if not isinstance(facts, list):
        errors.append("facts must be a list")
    elif not (2 <= len(facts) <= 4):
        errors.append(f"facts must have 2–4 items; got {len(facts)}")

    # At least one trap
    if not isinstance(traps, list):
        errors.append("traps must be a list")
    elif len(traps) < 1:
        errors.append("traps must have at least 1 item")

    # At least one official_docs URL
    if not isinstance(official_docs, list):
        errors.append("official_docs must be a list")
    else:
        valid_urls = [u for u in official_docs if _AWS_DOCS_RE.match(str(u).strip())]
        if len(valid_urls) < 1:
            errors.append("official_docs must contain at least one docs.aws.amazon.com URL")

    return errors


# ---------------------------------------------------------------------------
# Concept-object validation (post-dataclass construction)
# ---------------------------------------------------------------------------


def _validate_object(c: Concept) -> list[str]:
    errors: list[str] = []

    if not c.id.strip():
        errors.append("id is required and must be a non-empty string")
    elif not _ID_RE.match(c.id.strip()):
        errors.append("id must be stable kebab-case")
    if not c.domain.strip():
        errors.append("domain is required and must be a non-empty string")
    elif c.domain.strip() not in _VALID_DOMAINS:
        errors.append(f"domain must be one of {sorted(_VALID_DOMAINS)}")
    if not c.task_statement.strip():
        errors.append("task_statement is required and must be a non-empty string")
    if not c.lesson_reference.strip():
        errors.append("lesson_reference is required and must be a non-empty string")
    if not c.expected_answer_criteria.strip():
        errors.append("expected_answer_criteria is required and must be a non-empty string")
    if not isinstance(c.ready, bool):
        errors.append("ready must be a boolean")

    if not (2 <= len(c.facts) <= 4):
        errors.append(f"facts must have 2–4 items; got {len(c.facts)}")

    if len(c.traps) < 1:
        errors.append("traps must have at least 1 item")

    valid_urls = [u for u in c.official_docs if _AWS_DOCS_RE.match(u.strip())]
    if len(valid_urls) < 1:
        errors.append("official_docs must contain at least one docs.aws.amazon.com URL")

    return errors
