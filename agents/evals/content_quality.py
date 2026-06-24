"""Phase 9.7 runnable content-quality eval.

Per the reviewer MUST_FIX item 3, the runnable eval samples ready concept
packets (not legacy artifact topics) and grounds Sage against the packet
links via the post-9.5 contract:

  * Concepts come from ``concepts.loader.load_all_concepts`` so only
    ``ready=True`` packets are exercised across every DVA-C02 domain.
  * Sage grounding is invoked with ``official_docs``,
    ``skill_builder_links`` and ``lab_links`` from the curated packet,
    so the citation list is packet-only — no service-name fallback
    URLs and no auto-minted exam-guide URLs can leak into the sample.
  * The sample payload carries the resolved ``concept_record`` so
    ``analyze()`` enforces packet-only URLs strictly.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

AGENTS_DIR = Path(__file__).resolve().parent.parent
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

from concepts.loader import load_all_concepts
from concepts.packet import concept_packet_fields
from evals.checks import analyze
from evals.reporting import write_reports
from exam_artifacts.loader import load_artifact_from_file, validate_artifact_shape
from prompts.rex import MODEL, build_rex_challenge_prompt
from sage_sources import load_sage_grounding

REPORT_DIR = AGENTS_DIR / "reports" / "evals"


def main() -> int:
    args = _parse_args()
    artifact = load_artifact_from_file(args.exam_id)
    shape_errors = validate_artifact_shape(artifact)
    concepts = _ready_concepts(args.exam_id, args.max_topics)
    targets = [_concept_target(concept) for concept in concepts]
    samples = []
    for target in targets:
        for index in range(args.samples_per_topic):
            samples.append(_sample(args.exam_id, target, index + 1, args.mode))

    report = analyze(
        exam_id=args.exam_id,
        artifact=artifact,
        targets=targets,
        samples=samples,
        artifact_shape_errors=shape_errors,
        partial=bool(args.max_topics),
    )
    json_path, markdown_path = write_reports(report, REPORT_DIR)
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")
    return 0 if report["overall_status"] == "pass" else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run content-quality evals for an exam artifact.")
    parser.add_argument("--exam-id", default="dva-c02")
    parser.add_argument("--samples-per-topic", type=int, default=1)
    parser.add_argument("--max-topics", type=int, default=0)
    parser.add_argument("--mode", choices=("mock", "live"), default="mock")
    return parser.parse_args()


def _ready_concepts(exam_id: str, max_topics: int) -> list[dict[str, Any]]:
    """Return ready concept packets for the exam, sorted deterministically.

    Sorted by ``(domain, id)`` so the runnable eval visits concepts in a
    predictable order across all four DVA-C02 domains.
    """
    try:
        concepts = load_all_concepts(exam_id)
    except FileNotFoundError:
        return []
    concepts = [c for c in concepts if c.get("ready", False)]
    concepts.sort(key=lambda c: (str(c.get("domain", "")), str(c.get("id", ""))))
    return concepts[:max_topics] if max_topics else concepts


def _concept_target(concept: dict[str, Any]) -> dict[str, Any]:
    """Adapt a concept record into the ``target`` shape ``analyze`` expects."""
    fields = concept_packet_fields(concept)
    return {
        "domain": concept.get("domain", ""),
        "domain_weight": 0,
        "topic_id": fields["topic_id"],
        "topic": fields["topic"],
        "task_statement_id": fields["task_statement_id"],
        "task_statement": concept.get("task_statement", ""),
        "services": fields["services"],
        "source_ids": fields["source_ids"],
        "concept_id": concept.get("id", ""),
    }


def _sample(exam_id: str, target: dict[str, Any], sample_index: int, mode: str) -> dict[str, Any]:
    concept = _concept_for_target(exam_id, target)
    fields = concept_packet_fields(concept)
    system, user = build_rex_challenge_prompt(
        exam_id=exam_id,
        domain=target["domain"],
        topic=target["topic"],
        task_statement=target["task_statement"],
        services=target["services"],
        source_ids=target["source_ids"],
    )
    challenge = _live_challenge(system, user) if mode == "live" else _mock_challenge(target, sample_index)
    grounding = load_sage_grounding(
        exam_id=exam_id,
        topic_id=target["topic_id"],
        topic=target["topic"],
        services=target["services"],
        source_ids=target["source_ids"],
        official_docs=fields["official_docs"],
        skill_builder_links=fields["skill_builder_links"],
        lab_links=fields["lab_links"],
    )
    return {
        "id": f"{target['topic_id']}#{sample_index}",
        "target": target,
        "concept_record": concept,
        "challenge": challenge,
        "prompt": {"system": system, "user": user},
        "citations": grounding["citations"],
    }


def _concept_for_target(exam_id: str, target: dict[str, Any]) -> dict[str, Any]:
    """Resolve the curated concept record used to build this sample."""
    from concepts.loader import find_concept

    return find_concept(exam_id, target["topic_id"])


def _mock_challenge(target: dict[str, Any], sample_index: int) -> dict[str, str]:
    service = target["services"][0] if target["services"] else "the platform"
    return {
        # concept_id is included so the runnable eval exercises the same
        # packet-id enforcement that live Rex output goes through.
        "concept_id": target.get("concept_id") or target.get("topic_id", ""),
        "domain": target["domain"],
        "topic": target["topic"],
        "scenario": (
            f"Mock eval sample {sample_index}: an engineer is validating {target['topic']} "
            f"with {service} before a certification review."
        ),
        "question": f"Which implementation choice best satisfies {target['task_statement']}?",
    }


def _live_challenge(system: str, user: str) -> dict[str, Any]:
    from langchain_core.messages import HumanMessage, SystemMessage

    from llm import get_llm

    response = get_llm(MODEL).invoke([SystemMessage(content=system), HumanMessage(content=user)])
    raw = response.content if isinstance(response.content, str) else str(response.content)
    try:
        return json.loads(_strip_code_fences(raw))
    except json.JSONDecodeError:
        return {"_raw": raw}


def _strip_code_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\n?|```$", "", text, flags=re.MULTILINE).strip()


if __name__ == "__main__":
    raise SystemExit(main())
