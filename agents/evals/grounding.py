"""Phase 9.7 — resource-grounding eval harness.

Three independent per-sample checks the eval gate runs before Phase 9 can
close:

* ``check_resource_grounding`` — every Sage citation must come from the
  active concept packet (``official_docs`` + ``skill_builder_links`` +
  ``lab_links``). URLs from anywhere else fail.
* ``check_concept_id_match`` — Rex's challenge topic and concept_id must
  match the selected concept, so a free-roaming LLM cannot drift the
  challenge off-packet.
* ``check_evaluator_miss_tracking`` — evaluator output must include the
  ``missed_criteria`` and ``triggered_traps`` lists (Phase 9.6 internal
  concept-miss audit). Missing or non-list values fail.

``analyze()`` in ``evals.checks`` aggregates these per-sample checks into
the gate-level ``checks`` dict; if any sample fails, the overall_status
flips to ``fail``.
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

    The packet URL allow-list is the union of ``official_docs``,
    ``skill_builder_links`` and ``lab_links`` from the concept record that
    was active when the challenge was generated. Citations pointing
    anywhere else are flagged so the eval gate refuses to close Phase 9.

    When the resolved record has no packet link fields (legacy sample
    payloads or aggregate ``analyze()`` calls without an explicit
    ``concept_record``), the check falls back to ``known_good_url_roots``
    so we don't false-positive on legacy URL patterns. When the packet
    DOES contain links, packet matching is strict — the fallback roots
    are ignored so a fabricated URL like ``docs.aws.amazon.com/lambda/...``
    still fails even though it's on a known-good root.
    """
    packet_urls = _packet_url_allowlist(concept_record)
    packet_set = {url for url in packet_urls if url}
    use_packet_strict = bool(packet_set)

    def _is_allowed(url: str) -> bool:
        if use_packet_strict:
            return url in packet_set
        # Fallback mode: accept packet URLs (none) + known-good roots.
        if url in packet_set:
            return True
        return any(url.startswith(root) for root in known_good_url_roots)

    out_of_packet_links: list[str] = []
    for citation in citations or []:
        url = str(citation.get("url", "") or "")
        if not url:
            out_of_packet_links.append("<empty url>")
            continue
        if not _is_allowed(url):
            out_of_packet_links.append(url)

    # Also scan the Sage response body for URL strings that are not in the
    # allow-list; LLM responses sometimes paste raw URLs that bypass the
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

    A mismatch indicates either the LLM ignored the topic anchor or the
    node failed to echo the concept_id. Either way the challenge is no
    longer aligned with the user's selected topic and should fail the gate.
    """
    if not selected_concept:
        return {"pass": True, "mismatch": None, "note": "no concept_record available"}

    expected_id = str(selected_concept.get("id", "") or "")
    expected_topic = str(selected_concept.get("topic", "") or "").strip().lower()

    actual_id = str(challenge_concept_id or "")
    actual_topic = str(challenge_topic or "").strip().lower()

    id_mismatch = bool(expected_id) and bool(actual_id) and actual_id != expected_id
    topic_mismatch = bool(expected_topic) and bool(actual_topic) and actual_topic != expected_topic
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

    Phase 9.6 wires ``missed_criteria`` and ``triggered_traps`` into the
    per-exchange record so future routing and coaching can audit concept
    gaps. If the evaluator ever returns an outcome without populating these
    lists (even empty), the gate refuses to close the phase.

    When the caller does not supply ``evaluator_output`` (e.g. a sample that
    exercises only the resource-grounding check), the check is treated as
    "not applicable" and passes — the gate only fails on real evidence of
    regression, not on missing eval data.
    """
    if not evaluator_output:
        return {
            "pass": True,
            "missing_fields": [],
            "present_fields": [],
            "note": "evaluator_output not supplied; check not applicable",
        }
    # Field is "present" only if it is a list (defensive against bad payloads
    # like strings or null that would crash downstream persistence).
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
    supplied by the caller; this keeps older eval callers working.
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


def _packet_url_allowlist(concept_record: dict[str, Any] | None) -> list[str]:
    if not concept_record:
        return []
    allow: list[str] = []
    for field in _PACKET_LINK_FIELDS:
        for url in concept_record.get(field) or []:
            if url and url not in allow:
                allow.append(url)
    return allow
