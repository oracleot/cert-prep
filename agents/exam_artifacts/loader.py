"""File-system loader for exam artifacts.

JSON files in ``agents/data/exam_artifacts/<exam_id>.json`` are the source of
truth. The DB row is a runtime cache, populated by ``store.ensure_seeded()``.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "data" / "exam_artifacts"

_REQUIRED_TOP_LEVEL = {
    "exam_code",
    "canonical_name",
    "provider",
    "official_guide_url",
    "captured_at",
    "source_version",
    "domains",
}
_REQUIRED_DOMAIN = {"name", "weight", "task_statements", "topics"}


def _artifact_path(exam_id: str) -> Path:
    return ARTIFACT_DIR / f"{exam_id}.json"


def load_artifact_from_file(exam_id: str) -> dict[str, Any]:
    """Read the JSON artifact from disk. Raises FileNotFoundError if missing."""
    return json.loads(_artifact_path(exam_id).read_text(encoding="utf-8"))


def load_artifact_bytes(exam_id: str) -> bytes:
    return _artifact_path(exam_id).read_bytes()


def content_checksum(exam_id: str) -> str:
    """SHA-256 of the raw JSON file bytes (not canonicalised)."""
    return hashlib.sha256(load_artifact_bytes(exam_id)).hexdigest()


def list_artifact_files() -> list[str]:
    """Exam IDs that have a JSON artifact file on disk. Empty if dir missing."""
    if not ARTIFACT_DIR.exists():
        return []
    return sorted(p.stem for p in ARTIFACT_DIR.glob("*.json"))


def validate_artifact_shape(artifact: dict) -> list[str]:
    """Return validation errors. Empty list = valid."""
    errors: list[str] = []
    missing = _REQUIRED_TOP_LEVEL - set(artifact.keys())
    if missing:
        return [f"missing top-level keys: {sorted(missing)}"]
    domains = artifact["domains"]
    if not isinstance(domains, list) or not domains:
        return ["domains must be a non-empty list"]
    total_weight = 0
    for i, domain in enumerate(domains):
        if not isinstance(domain, dict):
            errors.append(f"domains[{i}] is not an object")
            continue
        missing_d = _REQUIRED_DOMAIN - set(domain.keys())
        if missing_d:
            errors.append(f"domains[{i}] missing keys: {sorted(missing_d)}")
            continue
        if not isinstance(domain["weight"], int) or not 0 < domain["weight"] <= 100:
            errors.append(f"domains[{i}].weight must be int 1..100")
        total_weight += domain["weight"]
        if not isinstance(domain["task_statements"], list):
            errors.append(f"domains[{i}].task_statements must be a list")
        if not isinstance(domain["topics"], list):
            errors.append(f"domains[{i}].topics must be a list")
    if total_weight != 100:
        errors.append(f"domain weights sum to {total_weight}, expected 100")
    return errors
