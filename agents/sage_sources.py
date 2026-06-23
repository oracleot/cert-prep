"""Sage grounding helpers — Phase 9.5 packet-only contract.

Pre-9.5, Sage could cite URLs minted from a service-name fallback
(``SERVICE_DOCS``) or auto-generated exam-guide pages. That allowed URLs
that were never curated for the active concept to leak into Sage's response.

The Phase 9.5 contract:

* ``load_sage_grounding`` returns **only** URLs drawn from the concept
  packet (``official_docs``, ``skill_builder_links``, ``lab_links``). No
  service-name fallback. No exam-guide URL minting.
* When the new link parameters are passed (the post-9.5 contract), the
  legacy snippet/exam-guide/service code is **not** invoked — even if
  ``services`` or ``source_ids`` would have produced citations.
* When the new link parameters are **omitted** (legacy callers like
  ``evals/content_quality.py``), the pre-9.5 legacy path runs unchanged
  so older callers keep working until they migrate.

The ``Citation`` TypedDict is re-exported from ``sage_sources_legacy`` so
existing imports stay valid.
"""
from __future__ import annotations

from typing import TypedDict

# Re-export Citation so `from sage_sources import Citation` keeps working
# for legacy callers and tests.
from sage_sources_legacy import (  # noqa: F401  (re-export)
    Citation,
    EXAM_GUIDE_ROOTS,
    SERVICE_DOCS,
    SNIPPETS_DIR,
    _dedupe,
    _exam_guide_citations,
    _is_verified_url,
    _load_snippet_file,
    _service_citations,
    _snippet_for,
)


NO_VERIFIED_SOURCE_MESSAGE = "No verified source was found for this topic."


class SageGrounding(TypedDict):
    source_context: str
    citations: list[Citation]


def load_sage_grounding(
    exam_id: str,
    topic_id: str,
    topic: str,
    services: list[str],
    source_ids: list[str],
    official_docs: list[str] | None = None,
    skill_builder_links: list[str] | None = None,
    lab_links: list[str] | None = None,
) -> SageGrounding:
    """Build a Sage grounding block from the active concept packet only.

    Post-9.5 call sites pass ``official_docs`` / ``skill_builder_links`` /
    ``lab_links`` from the concept record. With those present, citations
    are restricted to URLs from those three lists; the legacy snippet,
    exam-guide, and service fallback paths are not used.

    Legacy call sites that omit the three new parameters continue to use
    the pre-9.5 fallback (snippet file → exam-guide → service docs) so
    ``evals/content_quality.py`` keeps running unchanged.
    """
    packet_call = (
        official_docs is not None
        or skill_builder_links is not None
        or lab_links is not None
    )
    if packet_call:
        return _packet_only_grounding(
            topic=topic,
            topic_id=topic_id,
            official_docs=official_docs or [],
            skill_builder_links=skill_builder_links or [],
            lab_links=lab_links or [],
        )

    # Legacy path — preserved for ``evals/content_quality.py`` and any
    # older caller that hasn't been migrated to the packet-only contract.
    file_context, file_citations = _load_snippet_file(exam_id, topic_id)
    if file_citations:
        return {"source_context": file_context, "citations": file_citations}

    citations = _exam_guide_citations(exam_id, source_ids)
    citations.extend(_service_citations(services))
    citations = _dedupe(citations)[:4]

    if not citations:
        return {
            "source_context": NO_VERIFIED_SOURCE_MESSAGE,
            "citations": [],
        }

    lines = [f"Verified sources for {topic} ({topic_id}):"]
    for index, citation in enumerate(citations, start=1):
        snippet = _snippet_for(citation, topic, services)
        lines.append(f"[{index}] {citation['title']}\nURL: {citation['url']}\nSnippet: {snippet}")
    return {"source_context": "\n\n".join(lines), "citations": citations}


def _packet_only_grounding(
    topic: str,
    topic_id: str,
    official_docs: list[str],
    skill_builder_links: list[str],
    lab_links: list[str],
) -> SageGrounding:
    """Build a grounding block restricted to the active concept packet.

    URLs that did not come from the concept record are silently dropped.
    This is the only way citations enter Sage's prompt in Phase 9.5.
    """
    citations: list[Citation] = []
    for index, url in enumerate(official_docs):
        if not _is_https_url(url):
            continue
        citations.append({
            "title": f"{topic} — official docs [{index + 1}]",
            "url": url,
            "snippet_id": f"packet:official_docs:{topic_id}:{index}",
        })
    for index, url in enumerate(skill_builder_links):
        if not _is_https_url(url):
            continue
        citations.append({
            "title": f"{topic} — Skill Builder [{index + 1}]",
            "url": url,
            "snippet_id": f"packet:skill_builder:{topic_id}:{index}",
        })
    for index, url in enumerate(lab_links):
        if not _is_https_url(url):
            continue
        citations.append({
            "title": f"{topic} — hands-on lab [{index + 1}]",
            "url": url,
            "snippet_id": f"packet:lab_links:{topic_id}:{index}",
        })

    if not citations:
        return {
            "source_context": NO_VERIFIED_SOURCE_MESSAGE,
            "citations": [],
        }

    lines = [f"Verified packet sources for {topic} ({topic_id}):"]
    for index, citation in enumerate(citations, start=1):
        lines.append(
            f"[{index}] {citation['title']}\n"
            f"URL: {citation['url']}\n"
            f"Concept packet reference: {citation['snippet_id']}"
        )
    return {"source_context": "\n\n".join(lines), "citations": citations}


def _is_https_url(url: str) -> bool:
    """Accept only URLs that look like real curated links.

    Catches accidental empty strings, relative paths, ``javascript:``,
    or other obviously bad inputs that would slip past a plain
    truthiness check.
    """
    return bool(url) and url.startswith("https://")
