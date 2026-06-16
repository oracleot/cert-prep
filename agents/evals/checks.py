from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any

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
    checks = {
        "artifact_shape": not artifact_shape_errors,
        "challenge_json_shape": not shape_errors,
        "domain_topic_distribution": _distribution_ok(artifact, targets, partial),
        "duplicate_rate_below_10_percent": duplicate_rate < 0.10,
        "official_source_citations": not missing_citations,
        "non_dva_leakage": not leakage,
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
    return any(citation["url"].startswith("https://docs.aws.amazon.com/") for citation in sample["citations"])


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
