"""Phase 9.7 — resource-grounding eval harness.

Per-sample checks that gate Phase 9 closure:

* ``check_resource_grounding`` — every Sage citation must come from the
  active concept packet (official_docs / skill_builder_links / lab_links).
* ``check_concept_id_match`` — Rex's challenge topic + concept_id match
  the selected concept, so the LLM cannot drift the challenge off-packet.
* ``check_evaluator_miss_tracking`` — evaluator output includes the
  ``missed_criteria`` and ``triggered_traps`` lists (Phase 9.6 audit).

``analyze()`` in ``evals.checks`` aggregates these into the gate-level
``checks`` dict; any sample failure flips overall_status to ``fail``.

``KNOWN_GOOD_URL_ROOTS`` mirrors the roots used by
``_has_official_citation`` so aggregate ``analyze()`` runs gate
consistently on legacy sample payloads. Direct callers that pass an
explicit ``concept_record`` get strict packet matching.
"""
from __future__ import annotations

import re
from typing import Any

_PACKET_LINK_FIELDS = ("official_docs", "skill_builder_links", "lab_links")
_MISS_FIELDS = ("missed_criteria", "triggered_traps")
_URL_PATTERN = re.compile(r"https?://[^\s)\]\"'<>]+")

KNOWN_GOOD_URL_ROOTS = (
    "https://docs.aws.amazon.com/",
    "https://docs.anthropic.com/",
    "https://modelcontextprotocol.io/",
    "https://claudecertifications.com/",
    "https://skillbuilder.aws/",
    "https://aws.amazon.com/",
)


def check_resource_grounding(
    challenge: dict[str, Any],
    concept_record: dict[str, Any] | None,
    sage_response: str,
    citations: list[dict[str, Any]],
    known_good_url_roots: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Fail when Sage cites URLs that did not come from the concept packet.

    When the packet has links, matching is strict (fallback roots ignored
    so a fabricated AWS URL still fails). When the packet is empty (legacy
    sample payloads), the check falls back to ``known_good_url_roots`` to
    avoid false positives on legacy URL patterns.
    """
    packet_set = {url for url in _packet_url_allowlist(concept_record) if url}
    strict = bool(packet_set)

    def _is_allowed(url: str) -> bool:
        if strict:
            return url in packet_set
        return url in packet_set or any(url.startswith(r) for r in known_good_url_roots)

    out_of_packet_links = [
        url for url in (str(c.get("url", "") or "") for c in (citations or []))
        if not url or not _is_allowed(url)
    ]
    if out_of_packet_links and "<empty url>" in out_of_packet_links and not any(
        u for u in out_of_packet_links if u
    ):
        out_of_packet_links = ["<empty url>"]

    # Also scan the Sage response body for inline URLs that bypass the
    # citation pipeline.
    inline_urls = _URL_PATTERN.findall(sage_response or "")
    fake_link_failures = [url for url in inline_urls if not _is_allowed(url)]

    passed = not out_of_packet_links and not fake_link_failures
    return {
        "pass": passed,
        "out_of_packet_links": out_of_packet_links,
        "fake_link_failures": fake_link_failures,
        "allowed_packet_urls": sorted(packet_set),
    }


def check_concept_id_match(
    challenge_topic: str,
    challenge_concept_id: str,
    selected_concept: dict[str, Any] | None,
) -> dict[str, Any]:
    """Fail when Rex's challenge drifted off the selected concept packet."""
    if not selected_concept:
        return {"pass": True, "mismatch": None, "note": "no concept_record available"}

    expected_id = str(selected_concept.get("id", "") or "")
    expected_topic = str(selected_concept.get("topic", "") or "").strip().lower()
    actual_id = str(challenge_concept_id or "")
    actual_topic = str(challenge_topic or "").strip().lower()

    id_mismatch = bool(expected_id) and bool(actual_id) and actual_id != expected_id
    topic_mismatch = (
        bool(expected_topic) and bool(actual_topic) and actual_topic != expected_topic
    )
    passed = not id_mismatch and not topic_mismatch

    return {
        "pass": passed,
        "expected_concept_id": expected_id,
        "actual_concept_id": actual_id,
        "expected_topic": expected_topic,
        "actual_topic": actual_topic,
        "mismatch": None if passed else {
            "id_mismatch": id_mismatch,
            "topic_mismatch": topic_mismatch,
        },
    }


def check_evaluator_miss_tracking(
    evaluator_output: dict[str, Any] | None,
    concept_record: dict[str, Any] | None,
) -> dict[str, Any]:
    """Fail when evaluator output is missing the internal miss-tracking fields.

    When ``evaluator_output`` is not supplied (e.g. aggregate sample
    exercising only resource-grounding), the check is treated as "not
    applicable" and passes — the gate fails only on real evidence of
    regression, not on missing eval data.
    """
    if not evaluator_output:
        return {
            "pass": True,
            "missing_fields": [],
            "present_fields": [],
            "note": "evaluator_output not supplied; check not applicable",
        }
    list_present = [
        field for field in _MISS_FIELDS
        if isinstance(evaluator_output.get(field), list)
    ]
    missing = [field for field in _MISS_FIELDS if field not in list_present]
    return {
        "pass": not missing,
        "missing_fields": missing,
        "present_fields": list_present,
        "concept_id": (concept_record or {}).get("id", ""),
    }


def concept_record_for_sample(sample: dict[str, Any]) -> dict[str, Any] | None:
    """Best-effort lookup of the concept record a sample was generated for.

    Falls back to the ``target`` payload when ``concept_record`` is not
    supplied by the caller.
    """
    if sample.get("concept_record"):
        return sample["concept_record"]
    target = sample.get("target") or {}
    if not target:
        return None
    return {
        "id": target.get("topic_id", ""),
        "topic": target.get("topic", ""),
        "domain": target.get("domain", ""),
        "official_docs": [],
        "skill_builder_links": [],
        "lab_links": [],
    }


def resolve_concept_record(exam_id: str, sample: dict[str, Any]) -> dict[str, Any] | None:
    """Pick the most authoritative concept record available for a sample.

    Order:
      1. ``sample["concept_record"]`` if the caller passed one explicitly.
      2. The bare fallback built from ``target`` (no packet links).

    Note: direct callers get strict packet matching. The aggregate
    ``analyze()`` path tolerates URLs from ``KNOWN_GOOD_URL_ROOTS``
    fallback when the resolved record has no link fields. YAML lookup is
    intentionally NOT used here because aggregate samples can carry URLs
    from a different concept revision than the curated YAML, and the
    gate's job at this layer is to flag URLs that aren't on a known-good
    root, not to enforce per-revision packet match.
    """
    explicit = sample.get("concept_record")
    if explicit:
        return explicit
    return concept_record_for_sample(sample)


def _packet_url_allowlist(concept_record: dict[str, Any] | None) -> list[str]:
    if not concept_record:
        return []
    allow: list[str] = []
    for field in _PACKET_LINK_FIELDS:
        for url in concept_record.get(field) or []:
            if url and url not in allow:
                allow.append(url)
    return allow
