"""Back-compat shims for the DVA-C02 curriculum pipeline.

The hardcoded ``_DVA_C02_DOMAINS`` literal that used to live here is now in
``agents/data/exam_artifacts/dva-c02.json`` (see ``agents/exam_artifacts``).
The JSON file is the source of truth; this module is the sync read path used
by code that has not been migrated to async artifact lookups yet.
"""
from __future__ import annotations

import logging
from copy import deepcopy

from exam_artifacts import load_artifact_from_file

logger = logging.getLogger(__name__)

DEFAULT_EXAM_ID = "dva-c02"


def default_blueprint() -> list[dict]:
    """Return the DVA-C02 blueprint domains (sync, file-based)."""
    return _artifact_domains(DEFAULT_EXAM_ID)


def default_curriculum() -> list[dict]:
    """Return a curriculum-shaped list with ``study_order`` and ``performance_score``."""
    domains = default_blueprint()
    for index, domain in enumerate(domains, start=1):
        domain["study_order"] = index
        domain["performance_score"] = 0
    return domains


def _artifact_domains(exam_id: str) -> list[dict]:
    try:
        artifact = load_artifact_from_file(exam_id)
        return deepcopy(artifact.get("domains", []))
    except FileNotFoundError:
        logger.warning("No artifact file for %s; returning empty blueprint.", exam_id)
        return []
