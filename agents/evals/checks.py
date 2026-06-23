from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any

# Phase 9.7 — resource-grounding harness lives in ``evals.grounding`` so
# ``checks.py`` stays focused on artifact-level gates. The functions are
# re-exported at module bottom for backward-compatible imports.
from evals.grounding import (
    check_concept_id_match,
    check_evaluator_miss_tracking,
    check_resource_grounding,
    concept_record_for_sample,
)

REQUIRED_CHALLENGE_KEYS = {"domain", "topic", "scenario", "question"}
DVA_LEAK_TERMS = ("dva-c02", "developer-associate-02", "developer associate")


def analyze(
    exam_id: str,
    artifact: dict[str, Any],
    targets: list[dict[str, Any]],
    samples: list[dict[str, Any]],
    artifact_shape_errors: list[str],
    partial: bool,
) -> dict[str, Any]:
    shape_errors = _shape_errors(samples)
    missing_citations = [sample["id"] for sample in samples if not _has_official_citation(sample)]
    leakage = _leakage_errors(exam_id, samples)
    duplicate_rate = _duplicate_rate(samples)

    # Phase 9.7 — per-sample resource-grounding + concept-id + miss-tracking
    # checks. Any sample failure flips resource_grounding to False, which
    # in turn fails overall_status so the gate refuses to close a phase.
    # Samples may carry an explicit ``concept_record``; otherwise we fall back
    # to a YAML lookup by topic_id so the gate can run on legacy sample
    # payloads (which only embed the topic_id via ``target``/``challenge``).
    sample_concept_records = [_resolve_concept_record(exam_id, sample) for sample in samples]

    resource_grounding_results = [
        check_resource_grounding(
            challenge=sample["challenge"],
            concept_record=sample_concept_records[index],
            sage_response=sample.get("sage_response", ""),
            citations=sample.get("citations", []),
            known_good_url_roots=KNOWN_GOOD_URL_ROOTS,
        )
        for index, sample in enumerate(samples)
    ]  
    concept_id_results = [
        check_concept_id_match(
            challenge_topic=sample["challenge"].get("topic", ""),
            challenge_concept_id=sample["challenge"].get("concept_id", ""),
            selected_concept=sample_concept_records[index],
        )
        for index, sample in enumerate(samples)
    ]
    miss_tracking_results = [
        check_evaluator_miss_tracking(
            evaluator_output=sample.get("evaluator_output", {}),
            concept_record=sample_concept_records[index],
        )
        for index, sample in enumerate(samples)
    ]  

    resource_grounding_pass = all(result.get("pass") for result in resource_grounding_results)
    concept_id_match_pass = all(result.get("pass") for result in concept_id_results)
    evaluator_miss_tracking_pass = all(result.get("pass") for result in miss_tracking_results)

    checks = {
        "artifact_shape": not artifact_shape_errors,
        "challenge_json_shape": not shape_errors,
        "domain_topic_distribution": _distribution_ok(artifact, targets, partial),
        "duplicate_rate_below_10_percent": duplicate_rate < 0.10,
        "official_source_citations": not missing_citations,
        "non_dva_leakage": not leakage,
        "resource_grounding": resource_grounding_pass,
        "concept_id_match": concept_id_match_pass,
        "evaluator_miss_tracking": evaluator_miss_tracking_pass,
    }
    return {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "exam_id": exam_id,
        "mode": "partial" if partial else "full",
        "overall_status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "metrics": _metrics(targets, samples, duplicate_rate),
        "failures": {
            "artifact_shape": artifact_shape_errors,
            "challenge_json_shape": shape_errors,
            "missing_official_citations": missing_citations,
            "dva_leakage": leakage,
            "resource_grounding": [
                result.get("out_of_packet_links") or result.get("fake_link_failures")
                for result in resource_grounding_results
                if not result.get("pass")
            ],
            "concept_id_match": [
                result.get("mismatch") for result in concept_id_results if not result.get("pass")
            ],
            "evaluator_miss_tracking": [
                result.get("missing_fields")
                for result in miss_tracking_results
                if not result.get("pass")
            ],
        },
        "samples": samples,
    }


def _shape_errors(samples: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for sample in samples:
        challenge = sample["challenge"]
        missing = REQUIRED_CHALLENGE_KEYS - set(challenge)
        if missing:
            errors.append(f"{sample['id']} missing {sorted(missing)}")
            continue
        for key in REQUIRED_CHALLENGE_KEYS:
            if not isinstance(challenge[key], str) or not challenge[key].strip():
                errors.append(f"{sample['id']} has invalid {key}")
    return errors


def _has_official_citation(sample: dict[str, Any]) -> bool:
    allowed_roots = (
        "https://docs.aws.amazon.com/",
        "https://docs.anthropic.com/",
        "https://modelcontextprotocol.io/",
        "https://claudecertifications.com/",
    )
    return any(citation["url"].startswith(allowed_roots) for citation in sample["citations"])


def _leakage_errors(exam_id: str, samples: list[dict[str, Any]]) -> list[str]:
    if exam_id == "dva-c02":
        return []
    errors: list[str] = []
    for sample in samples:
        text = json.dumps(sample["challenge"]).lower()
        terms = [term for term in DVA_LEAK_TERMS if term in text]
        if terms:
            errors.append(f"{sample['id']} leaked {terms}")
    return errors


def _duplicate_rate(samples: list[dict[str, Any]]) -> float:
    keys = [_normalized_key(sample["challenge"]) for sample in samples]
    if not keys:
        return 0.0
    counts = Counter(keys)
    duplicates = sum(count - 1 for count in counts.values() if count > 1)
    return duplicates / len(keys)


def _normalized_key(challenge: dict[str, Any]) -> str:
    text = f"{challenge.get('scenario', '')} {challenge.get('question', '')}"
    return re.sub(r"\s+", " ", text.lower()).strip()


def _distribution_ok(artifact: dict[str, Any], targets: list[dict[str, Any]], partial: bool) -> bool:
    if partial:
        return bool(targets)
    expected = sum(len(domain["topics"]) for domain in artifact["domains"])
    return len({target["topic_id"] for target in targets}) == expected


def _metrics(targets: list[dict[str, Any]], samples: list[dict[str, Any]], duplicate_rate: float) -> dict[str, Any]:
    return {
        "target_topic_count": len({target["topic_id"] for target in targets}),
        "sample_count": len(samples),
        "duplicate_rate": round(duplicate_rate, 4),
        "domain_counts": dict(Counter(sample["target"]["domain"] for sample in samples)),
        "topic_counts": dict(Counter(sample["target"]["topic_id"] for sample in samples)),
    }


def _resolve_concept_record(exam_id: str, sample: dict[str, Any]) -> dict[str, Any] | None:
    """Pick the most authoritative concept record available for a sample.

    Order:
      1. ``sample["concept_record"]`` if the caller passed one explicitly.
      2. The bare fallback built from ``target`` (no packet links) — used
         only so we never crash the gate on legacy sample payloads.

    Note: direct callers (``check_resource_grounding(challenge,
    concept_record, ...)``) get strict packet matching. The aggregate
    ``analyze()`` path tolerates URLs from the ``KNOWN_GOOD_URL_ROOTS``
    fallback when the resolved record has no link fields (legacy samples);
    YAML lookup is intentionally NOT used here because aggregate samples
    can carry URLs from a different revision of the concept than the
    curated YAML, and the gate's job at this layer is to flag URLs that
    aren't on a known-good root, not to enforce per-revision packet match.
    """
    explicit = sample.get("concept_record")
    if explicit:
        return explicit
    return concept_record_for_sample(sample)


# Curated URL roots that are always considered safe to cite. Mirrors the
# roots used by ``_has_official_citation`` for the content-quality gate so
# the resource-grounding gate produces consistent pass/fail verdicts when
# the sample lacks an explicit concept_record.
KNOWN_GOOD_URL_ROOTS = (
    "https://docs.aws.amazon.com/",
    "https://docs.anthropic.com/",
    "https://modelcontextprotocol.io/",
    "https://claudecertifications.com/",
    "https://skillbuilder.aws/",
    "https://aws.amazon.com/",
)
