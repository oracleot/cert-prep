from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_reports(report: dict[str, Any], report_dir: Path) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    base = report_dir / f"{report['run_id']}-{report['exam_id']}-content-quality"
    json_path = base.with_suffix(".json")
    markdown_path = base.with_suffix(".md")
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    markdown_path.write_text(_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def _markdown(report: dict[str, Any]) -> str:
    checks = "\n".join(
        f"- [{'x' if passed else ' '}] {name.replace('_', ' ')}"
        for name, passed in report["checks"].items()
    )
    metrics = "\n".join(f"- {key}: {value}" for key, value in report["metrics"].items())
    failures = _failure_section(report["failures"])
    return f"""# Content Quality Eval: {report['exam_id']}

Run: `{report['run_id']}`
Status: **{report['overall_status'].upper()}**
Scope: {report['mode']}

## Automated Checks

{checks}

## Metrics

{metrics}

## Failures

{failures}

## Human Review Rubric

Score each sampled challenge and Sage response 1-5.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| Challenge realism | Toy or implausible | Plausible but generic | Operationally specific and exam-like |
| Exam relevance | Off-blueprint | Related but shallow | Directly tests the target domain/topic |
| Source grounding | No official source trail | Source exists but weakly connected | Claim maps clearly to AWS docs/guide |
| Sage correctness | Factually wrong | Mostly right with gaps | Correct, precise, and cites official docs |
| Difficulty fit | Mismatched | Close | Matches requested difficulty |

Manual pass bar: average >= 4.0 and no Sage correctness score below 3.
"""


def _failure_section(failures: dict[str, list[str]]) -> str:
    lines: list[str] = []
    for name, values in failures.items():
        if not values:
            lines.append(f"- {name}: none")
            continue
        preview = "; ".join(values[:10])
        suffix = "" if len(values) <= 10 else f"; +{len(values) - 10} more"
        lines.append(f"- {name}: {preview}{suffix}")
    return "\n".join(lines)
