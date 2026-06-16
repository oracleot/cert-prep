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
    targets = _targets(artifact, args.max_topics)
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


def _targets(artifact: dict[str, Any], max_topics: int) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for domain in artifact["domains"]:
        tasks = {task["id"]: task["text"] for task in domain["task_statements"]}
        for topic in domain["topics"]:
            targets.append(
                {
                    "domain": domain["name"],
                    "domain_weight": domain["weight"],
                    "topic_id": topic["id"],
                    "topic": topic["name"],
                    "task_statement_id": topic["task_statement_id"],
                    "task_statement": tasks.get(topic["task_statement_id"], ""),
                    "services": topic["services"],
                    "source_ids": topic["source_ids"],
                }
            )
    return targets[:max_topics] if max_topics else targets


def _sample(exam_id: str, target: dict[str, Any], sample_index: int, mode: str) -> dict[str, Any]:
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
    )
    return {
        "id": f"{target['topic_id']}#{sample_index}",
        "target": target,
        "challenge": challenge,
        "prompt": {"system": system, "user": user},
        "citations": grounding["citations"],
    }


def _mock_challenge(target: dict[str, Any], sample_index: int) -> dict[str, str]:
    service = target["services"][0] if target["services"] else "AWS"
    return {
        "domain": target["domain"],
        "topic": target["topic"],
        "scenario": (
            f"Mock eval sample {sample_index}: an engineer is validating {target['topic']} "
            f"with {service} before an AWS certification review."
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
