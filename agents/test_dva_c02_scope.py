"""Phase 9.2 AC1–AC2: domain + task-statement scope.

Fails against Phase 9.1 (only 2 ready records exist, no full coverage).
Passes when all four domains and all 13 task statements are curated.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from concepts.loader import CONCEPTS_DIR

DVA_C02_DIR = CONCEPTS_DIR / "dva-c02"
FIXTURE_PREFIX = "invalid-"
_DOMAINS = {"Development", "Security", "Deployment", "Troubleshooting"}


def _production_yaml_files() -> list[Path]:
    return sorted(
        p for p in DVA_C02_DIR.glob("*.yaml")
        if p.name != "_coverage.yaml"
        and not p.name.startswith(FIXTURE_PREFIX)
    )


def _load_production_records() -> list[dict]:
    records: list[dict] = []
    for path in _production_yaml_files():
        with path.open() as fh:
            data = yaml.safe_load(fh)
        if isinstance(data, list):
            records.extend(data)
        elif isinstance(data, dict):
            records.append(data)
    return records


# ---------------------------------------------------------------------------
# AC1 – all four domains represented
# ---------------------------------------------------------------------------

class TestDomainCoverage:
    def test_all_four_domains_have_ready_concept(self) -> None:
        records = _load_production_records()
        domains = {r["domain"] for r in records if r.get("ready", False)}
        missing = _DOMAINS - domains
        assert not missing, (
            f"Domains with no ready concept: {sorted(missing)}. "
            f"Found: {sorted(domains)}"
        )


# ---------------------------------------------------------------------------
# AC2 – all 13 task statements represented
# ---------------------------------------------------------------------------

_TASK_KEYWORDS: dict[str, tuple[str, ...]] = {
    "1.1": ("applications hosted on AWS", "Develop code for applications hosted on AWS"),
    "1.2": ("Develop code for AWS Lambda", "code for AWS Lambda"),
    "1.3": ("data stores in application development", "Use data stores"),
    "2.1": ("Implement authentication", "authentication and/or authorization"),
    "2.2": ("Implement encryption by using", "encryption by using AWS services"),
    "2.3": ("Manage sensitive data in application code", "sensitive data in application code"),
    "3.1": ("Prepare application artifacts", "artifacts to be deployed to AWS"),
    "3.2": ("Test applications in development environments", "testing deployed code"),
    "3.3": ("Automate deployment testing", "automate deployment testing"),
    "3.4": ("Deploy code by using AWS CI/CD", "CI/CD"),
    "4.1": ("Assist in a root cause analysis", "root cause analysis"),
    "4.2": ("Instrument code for observability", "instrument code"),
    "4.3": ("Optimize applications by using AWS services", "optimize applications"),
}


class TestTaskStatementCoverage:
    @pytest.mark.parametrize(
        "ts_id,keywords", list(_TASK_KEYWORDS.items()),
        ids=list(_TASK_KEYWORDS.keys()),
    )
    def test_task_statement_covered(self, ts_id: str, keywords: tuple[str, ...]) -> None:
        records = [r for r in _load_production_records() if r.get("ready", False)]
        matched = [
            r["id"] for r in records
            if any(kw.lower() in str(r.get("task_statement", "")).lower()
                   for kw in keywords)
        ]
        assert matched, (
            f"Task statement {ts_id} not covered. Need at least one concept "
            f"with task_statement containing one of: {keywords}"
        )
