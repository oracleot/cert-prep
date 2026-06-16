from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import Literal

from exam_artifacts import (
    content_checksum,
    get_artifact,
    load_artifact_from_file,
    validate_artifact_shape,
    validate_exam_id,
)

logger = logging.getLogger(__name__)

BlueprintSource = Literal["cache", "official_source", "rejected"]


@dataclass(frozen=True)
class BlueprintScoutResult:
    accepted: bool
    exam_id: str
    canonical_name: str
    domains: list[dict]
    source: BlueprintSource
    message: str


async def resolve_blueprint(raw_exam: str) -> BlueprintScoutResult:
    """Resolve an onboarding exam code to a trusted blueprint artifact.

    The curated artifact JSONs are the official-source boundary for V1. The DB
    row is only a runtime cache; if the cache is absent or stale, Scout refreshes
    from the checked-in artifact and refuses to continue on validation errors.
    """
    validation = validate_exam_id(raw_exam)
    if not validation.accepted:
        return BlueprintScoutResult(
            accepted=False,
            exam_id=validation.exam_id,
            canonical_name="",
            domains=[],
            source="rejected",
            message=validation.message,
        )

    cached = await _load_valid_cache(validation.exam_id)
    if cached:
        return BlueprintScoutResult(
            accepted=True,
            exam_id=validation.exam_id,
            canonical_name=cached["canonical_name"],
            domains=deepcopy(cached["domains"]),
            source="cache",
            message=f"Loaded {cached['canonical_name']} from the blueprint cache.",
        )

    try:
        artifact = load_artifact_from_file(validation.exam_id)
    except (FileNotFoundError, ValueError) as exc:
        logger.warning("Blueprint artifact unavailable for %s: %s", validation.exam_id, exc)
        return BlueprintScoutResult(
            accepted=False,
            exam_id=validation.exam_id,
            canonical_name=validation.canonical_name,
            domains=[],
            source="rejected",
            message=(
                f"No parseable official-source artifact is available for "
                f"{validation.exam_id.upper()}."
            ),
        )

    errors = validate_artifact_shape(artifact)
    if errors:
        return BlueprintScoutResult(
            accepted=False,
            exam_id=validation.exam_id,
            canonical_name=validation.canonical_name,
            domains=[],
            source="rejected",
            message=f"Official-source artifact failed validation: {'; '.join(errors)}",
        )

    return BlueprintScoutResult(
        accepted=True,
        exam_id=validation.exam_id,
        canonical_name=artifact["canonical_name"],
        domains=deepcopy(artifact["domains"]),
        source="official_source",
        message=f"Refreshed {artifact['canonical_name']} from the official-source artifact.",
    )


async def _load_valid_cache(exam_id: str) -> dict | None:
    cached = await get_artifact(exam_id)
    if not cached:
        return None
    errors = validate_artifact_shape(cached)
    if errors:
        logger.warning("Ignoring invalid cached artifact %s: %s", exam_id, errors)
        return None
    try:
        if cached.get("content_checksum") != content_checksum(exam_id):
            return None
    except FileNotFoundError:
        return None
    return cached
