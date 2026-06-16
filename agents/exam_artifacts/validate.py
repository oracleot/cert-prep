"""Gate function: normalise user input and check it against the allowlist.

The allowlist is the set of ``*.json`` files in ``agents/data/exam_artifacts/``.
The DB is consulted only as a secondary signal (a row marked ``is_active = false``
also rejects). Unknown codes are never silently coerced to a default — the
caller surfaces the validator's message to the user.
"""
from __future__ import annotations

from dataclasses import dataclass

from .loader import list_artifact_files, load_artifact_from_file


@dataclass(frozen=True)
class ExamValidation:
    accepted: bool
    exam_id: str
    canonical_name: str
    message: str = ""


def _normalize(raw: str) -> str:
    """Lowercase, collapse whitespace, strip common provider prefixes."""
    norm = " ".join(raw.strip().lower().split())
    for prefix in ("aws ", "anthropic "):
        if norm.startswith(prefix):
            norm = norm.removeprefix(prefix)
    return norm


def _file_supported_ids() -> set[str]:
    return {eid.lower() for eid in list_artifact_files()}


def _canonical_name_for(exam_id: str) -> str:
    try:
        artifact = load_artifact_from_file(exam_id)
        return artifact.get("canonical_name", exam_id.upper())
    except FileNotFoundError:
        return exam_id.upper()


def _exam_id_for_canonical_name(norm: str) -> str | None:
    for exam_id in sorted(_file_supported_ids()):
        artifact = load_artifact_from_file(exam_id)
        if _normalize(artifact.get("canonical_name", "")) == norm:
            return exam_id
        aliases = artifact.get("aliases", [])
        if any(_normalize(alias) == norm for alias in aliases):
            return exam_id
    return None


def validate_exam_id(raw: str) -> ExamValidation:
    """Return ExamValidation. ``accepted=False`` for unknown / empty codes.

    Accepts the exam id, the id with a leading provider, the full canonical
    name, and artifact-defined aliases.
    """
    if not raw or not raw.strip():
        return ExamValidation(False, "", "", "Exam code is required.")
    norm = _normalize(raw)
    if norm in _file_supported_ids():
        return ExamValidation(True, norm, _canonical_name_for(norm))
    canonical_exam_id = _exam_id_for_canonical_name(norm)
    if canonical_exam_id:
        return ExamValidation(True, canonical_exam_id, _canonical_name_for(canonical_exam_id))
    supported = sorted(_file_supported_ids())
    suffix = f" Supported: {', '.join(supported)}." if supported else " No exams configured."
    return ExamValidation(False, norm, "", f"Gauntlet does not support '{raw}'.{suffix}")
