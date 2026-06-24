"""Phase 9.7 — resource-grounding eval harness.

Per-sample checks that gate Phase 9 closure:

* ``check_resource_grounding`` — every Sage citation must come from the
  active concept packet (official_docs / skill_builder_links / lab_links).
  No broad known-good URL root fallback: aggregate ``analyze()`` resolves
  ready concept packets and enforces packet-only URLs. The fallback only
  applies for samples with no resolvable packet (legacy fixtures).
* ``check_concept_id_match`` — Rex's challenge topic + concept_id match
  the selected concept, so the LLM cannot drift the challenge off-packet.
* ``check_evaluator_miss_tracking`` — evaluator output includes the
  ``missed_criteria`` and ``triggered_traps`` lists (Phase 9.6 audit).
  Missing ``evaluator_output`` is a failure; ``analyze()`` only treats
  the check as not-applicable when the sample omits the field.

``analyze()`` in ``evals.checks`` aggregates these into the gate-level
``checks`` dict; any sample failure flips overall_status to ``fail``.
"""
from __future__ import annotations

import re
from typing import Any

_PACKET_LINK_FIELDS = ("official_docs", "skill_builder_links", "lab_links")
_MISS_FIELDS = ("missed_criteria", "triggered_traps")
_URL_PATTERN = re.compile(r"https?://[^\s)\]\"'<>]+")


def check_resource_grounding(
    challenge: dict[str, Any],
    concept_record: dict[str, Any] | None,
    sage_response: str,
    citations: list[dict[str, Any]],
    known_good_url_roots: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Fail when Sage cites URLs that did not come from the concept packet.

    Strict packet-only matching is the default; ``known_good_url_roots``
    only applies when no packet URLs are available (legacy fixtures).
    """
    packet_set = {url for url in _packet_url_allowlist(concept_record) if url}
    strict = bool(packet_set)

    def _is_allowed(url: str) -> bool:
        if not url:
            return False
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
    """Fail when Rex's challenge drifted off the selected concept packet.

    A selected concept always carries an ``id`` (it's the curated packet's
    stable kebab-case identifier). When the challenge omits or blanks the
    concept_id, that's a Phase 9 regression — Rex was supposed to echo it
    verbatim. Treat that as a hard fail rather than a pass.
    """
    if not selected_concept:
        return {"pass": True, "mismatch": None, "note": "no concept_record available"}

    expected_id = str(selected_concept.get("id", "") or "")
    expected_topic = str(selected_concept.get("topic", "") or "").strip().lower()
    actual_id = str(challenge_concept_id or "")
    actual_topic = str(challenge_topic or "").strip().lower()

    id_mismatch = bool(expected_id) and actual_id != expected_id
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
    """Fail when evaluator output is missing or missing miss-tracking fields.

    Missing ``evaluator_output`` (None or empty dict) is a Phase 9 regression
    per the reviewer contract. ``analyze()`` only skips this check when the
    sample omits the field entirely.
    """
    if not evaluator_output:
        return {
            "pass": False,
            "missing_fields": list(_MISS_FIELDS),
            "present_fields": [],
            "concept_id": (concept_record or {}).get("id", ""),
            "note": "evaluator_output missing; miss tracking not verified",
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
    """Best-effort lookup of the concept record a sample was generated for."""
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
      2. The curated loader record matching ``target.topic_id`` or
         ``challenge.concept_id`` — so aggregate ``analyze()`` runs gate
         against the same concept packet Rex/Sage/Evaluator saw at
         runtime, instead of inheriting a ``known_good_url_roots``
         fallback.
      3. The bare fallback built from ``target`` for legacy fixtures.
    """
    explicit = sample.get("concept_record")
    if explicit:
        return explicit
    topic_id = (
        (sample.get("target") or {}).get("topic_id", "")
        or (sample.get("challenge") or {}).get("concept_id", "")
    )
    if topic_id:
        try:
            from concepts.loader import find_concept
            return find_concept(exam_id, topic_id)
        except (KeyError, ImportError, FileNotFoundError):
            pass
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
