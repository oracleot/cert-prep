"""Runtime helpers for loading, finding, and filtering concept records.

Records live as YAML files under ``agents/data/concepts/<exam_id>/``.
Only records that pass the quality gate are included in the index.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

CONCEPTS_DIR = Path(__file__).resolve().parent.parent / "data" / "concepts"

# ---------------------------------------------------------------------------
# Module-local index: populated lazily on first use
# ---------------------------------------------------------------------------

_INDEX: list[dict[str, Any]] | None = None
_INDEX_EXAM_ID: str | None = None


def _module_index(exam_id: str) -> list[dict[str, Any]]:
    """Load all validated YAML records for ``exam_id`` into a list.

    Only ``ready: true`` records survive the quality gate and enter the index.
    Invalid records are skipped silently in production; callers that need
    strict validation should call ``validate_concept`` directly on the raw
    dict before building a ``Concept``.
    """
    global _INDEX, _INDEX_EXAM_ID

    exam_dir = CONCEPTS_DIR / exam_id
    if not exam_dir.is_dir():
        raise FileNotFoundError(f"Concept directory not found: {exam_dir}")

    if _INDEX is None or _INDEX_EXAM_ID != exam_id:
        _INDEX = _load_all_raw(exam_id)
        _INDEX_EXAM_ID = exam_id

    return _INDEX


def _load_all_raw(exam_id: str) -> list[dict[str, Any]]:
    """Parse every .yaml file in ``CONCEPTS_DIR/<exam_id>/`` and validate."""
    from .validate import validate_concept

    exam_dir = CONCEPTS_DIR / exam_id
    if not exam_dir.is_dir():
        raise FileNotFoundError(f"Concept directory not found: {exam_dir}")

    records: list[dict[str, Any]] = []
    for path in sorted(exam_dir.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            continue  # skip empty / null files
        validation = validate_concept(raw)
        if validation.valid and raw.get("ready", False):
            records.append(raw)
    return records


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_AGENTS_DIR = Path(__file__).resolve().parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


def load_all_concepts(exam_id: str = "dva-c02") -> list[dict[str, Any]]:
    """Return all ready, valid concept records for ``exam_id``.

    Parameters
    ----------
    exam_id:
        Lower-case exam code.  Defaults to ``dva-c02``.

    Returns
    -------
    list[dict[str, Any]]
        Every YAML record under ``data/concepts/<exam_id>/`` whose ``ready``
        field is ``true`` and which passes the quality gate.
        Returns an empty list if the directory does not exist or no records
        qualify.
    """
    return list(_module_index(exam_id))


def find_concept(exam_id: str, concept_id: str) -> dict[str, Any]:
    """Return a single ready concept record by ``concept_id``.

    Parameters
    ----------
    exam_id:
        Lower-case exam code.
    concept_id:
        The record's ``id`` field.

    Returns
    -------
    dict[str, Any]
        The matching record.

    Raises
    ------
    KeyError
        When no ready, valid record with that ``id`` exists.
    """
    for record in _module_index(exam_id):
        if record.get("id") == concept_id:
            return record
    raise KeyError(f"No ready concept found with id={concept_id!r} for exam_id={exam_id!r}")


def filter_ready(
    concepts: list[dict[str, Any]],
    domain: str | None = None,
    exclude_unready: bool = True,
) -> list[dict[str, Any]]:
    """Filter a list of concept records.

    Parameters
    ----------
    concepts:
        Raw concept records (dicts), typically from ``load_all_concepts``.
    domain:
        If provided, restrict to records whose ``domain`` equals this value.
        Matching is case-sensitive.
    exclude_unready:
        If ``True`` (the default), drop any record where ``ready`` is not
        ``True``.

    Returns
    -------
    list[dict[str, Any]]
        Filtered list, preserving original order.
    """
    result = []
    for c in concepts:
        if exclude_unready and not c.get("ready", False):
            continue
        if domain is not None and c.get("domain") != domain:
            continue
        result.append(c)
    return result
