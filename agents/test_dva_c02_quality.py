"""Phase 9.2 AC3–AC4: schema validity + no transcript dumps.

Fails against Phase 9.1 (curated records are sparse / incomplete).
Passes when every production record is schema-valid and concept-level.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from concepts.validate import validate_concept

DVA_C02_DIR = Path(__file__).resolve().parent / "data" / "concepts" / "dva-c02"
FIXTURE_PREFIX = "invalid-"
MAX_FACT_CHARS = 300
MAX_TRAP_CHARS = 300
MAX_CRITERIA_CHARS = 600
MAX_FACTS = 4
MAX_TRAPS = 8


def _production_yaml_files() -> list[Path]:
    return sorted(
        p for p in DVA_C02_DIR.glob("*.yaml")
        if p.name != "_coverage.yaml"
        and not p.name.startswith(FIXTURE_PREFIX)
    )


# ---------------------------------------------------------------------------
# AC3 – schema validity
# ---------------------------------------------------------------------------

class TestSchemaValidity:
    @pytest.mark.parametrize("path", _production_yaml_files(), ids=lambda p: p.name)
    def test_valid_concept_record(self, path: Path) -> None:
        with path.open() as fh:
            data = yaml.safe_load(fh)
        records: list[dict] = data if isinstance(data, list) else [data]
        for record in records:
            result = validate_concept(record)
            assert result.valid, (
                f"[{path.name}] '{record.get('id', '?')}' failed:\n"
                + "\n".join(f"  • {e}" for e in result.errors)
            )

    def test_lesson_reference_populated(self) -> None:
        for path in _production_yaml_files():
            with path.open() as fh:
                data = yaml.safe_load(fh)
            records: list[dict] = data if isinstance(data, list) else [data]
            for r in records:
                if not r.get("ready", False):
                    continue
                lr = str(r.get("lesson_reference", "")).strip()
                assert lr, f"[{r.get('id')}] lesson_reference required on ready records"


# ---------------------------------------------------------------------------
# AC4 – no transcript dumps
# ---------------------------------------------------------------------------

class TestNoTranscriptDumps:
    @pytest.mark.parametrize("path", _production_yaml_files(), ids=lambda p: p.name)
    def test_facts_bounded(self, path: Path) -> None:
        with path.open() as fh:
            data = yaml.safe_load(fh)
        records: list[dict] = data if isinstance(data, list) else [data]
        for r in records:
            if not r.get("ready", False):
                continue
            facts = r.get("facts", [])
            assert len(facts) <= MAX_FACTS, (
                f"[{r.get('id')}] {len(facts)} facts > {MAX_FACTS} (transcript dump?)"
            )
            for i, fact in enumerate(facts):
                assert len(fact) <= MAX_FACT_CHARS, (
                    f"[{r.get('id')}] fact[{i}] {len(fact)}>{MAX_FACT_CHARS} chars: "
                    f"{fact[:60]!r}…"
                )

    @pytest.mark.parametrize("path", _production_yaml_files(), ids=lambda p: p.name)
    def test_traps_bounded(self, path: Path) -> None:
        with path.open() as fh:
            data = yaml.safe_load(fh)
        records: list[dict] = data if isinstance(data, list) else [data]
        for r in records:
            if not r.get("ready", False):
                continue
            traps = r.get("traps", [])
            assert len(traps) <= MAX_TRAPS, (
                f"[{r.get('id')}] {len(traps)} traps > {MAX_TRAPS} (transcript dump?)"
            )
            for i, trap in enumerate(traps):
                assert len(trap) <= MAX_TRAP_CHARS, (
                    f"[{r.get('id')}] trap[{i}] {len(trap)}>{MAX_TRAP_CHARS} chars: "
                    f"{trap[:60]!r}…"
                )

    @pytest.mark.parametrize("path", _production_yaml_files(), ids=lambda p: p.name)
    def test_criteria_bounded(self, path: Path) -> None:
        with path.open() as fh:
            data = yaml.safe_load(fh)
        records: list[dict] = data if isinstance(data, list) else [data]
        for r in records:
            if not r.get("ready", False):
                continue
            criteria = str(r.get("expected_answer_criteria", ""))
            assert len(criteria) <= MAX_CRITERIA_CHARS, (
                f"[{r.get('id')}] criteria {len(criteria)}>{MAX_CRITERIA_CHARS} chars "
                "(transcript dump?)"
            )
