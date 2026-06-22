"""Phase 9.2 AC5–AC7: coverage matrix exists, is complete, and honestly flags gaps.

Fails against Phase 9.1 (_coverage.yaml does not exist yet).
Passes when the coverage matrix is present and correctly structured.
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
COVERAGE_FILE = DVA_C02_DIR / "_coverage.yaml"


def _load_yaml(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    with path.open() as fh:
        return yaml.safe_load(fh)


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


def _flatten_matrix_ids(matrix: dict | list) -> list[str]:
    ids: list[str] = []
    if isinstance(matrix, dict):
        for v in matrix.values():
            if isinstance(v, list):
                for x in v:
                    if isinstance(x, dict):
                        ids.append(str(x.get("id", "")))
                    else:
                        ids.append(str(x))
            elif isinstance(v, str):
                ids.append(v)
    elif isinstance(matrix, list):
        for item in matrix:
            if isinstance(item, dict):
                ids.append(str(item.get("id", "")))
            else:
                ids.append(str(item))
    return ids


# ---------------------------------------------------------------------------
# AC5 – coverage matrix exists and is valid YAML
# ---------------------------------------------------------------------------

class TestCoverageMatrix:
    def test_file_exists(self) -> None:
        assert COVERAGE_FILE.exists(), (
            f"Missing: {COVERAGE_FILE}. Phase 9.2 requires this artifact."
        )

    def test_valid_yaml(self) -> None:
        data = _load_yaml(COVERAGE_FILE)
        assert data is not None
        assert isinstance(data, (dict, list)), (
            f"Must be a YAML dict or list, got {type(data).__name__}"
        )

    def test_every_production_concept_listed_once(self) -> None:
        """Every ready production ID appears exactly once in the matrix."""
        matrix = _load_yaml(COVERAGE_FILE)
        if matrix is None:
            pytest.skip("Coverage matrix does not exist")

        production_ids = {r["id"] for r in _load_production_records()}
        matrix_ids = _flatten_matrix_ids(matrix)

        matrix_id_set = set(matrix_ids)
        missing = production_ids - matrix_id_set
        dupes = [i for i in matrix_id_set if matrix_ids.count(i) > 1]
        assert not missing, f"Missing from matrix: {sorted(missing)}"
        assert not dupes, f"Duplicated in matrix: {dupes}"


# ---------------------------------------------------------------------------
# AC6 – invalid-* fixtures excluded
# ---------------------------------------------------------------------------

class TestCoverageMatrixExcludesFixtures:
    def test_invalid_prefix_not_in_matrix(self) -> None:
        matrix = _load_yaml(COVERAGE_FILE)
        if matrix is None:
            pytest.skip("Coverage matrix does not exist")

        fixture_ids = {
            p.stem for p in DVA_C02_DIR.glob("*.yaml")
            if p.stem.startswith("invalid-")
        }
        matrix_id_set = set(_flatten_matrix_ids(matrix))
        leaked = fixture_ids & matrix_id_set
        assert not leaked, (
            f"QA fixture IDs leaked into coverage matrix: {sorted(leaked)}. "
            "These invalid-* files are not production records."
        )


# ---------------------------------------------------------------------------
# AC7 – honestly flag missing links
# ---------------------------------------------------------------------------

class TestCoverageMatrixFlagsMissingLinks:
    def test_missing_official_docs_flagged(self) -> None:
        """Ready records without official_docs must have a status/flag in matrix."""
        matrix = _load_yaml(COVERAGE_FILE)
        if matrix is None:
            pytest.skip("Coverage matrix does not exist")

        ready = {r["id"]: r for r in _load_production_records() if r.get("ready", False)}

        entries: list[dict] = []
        if isinstance(matrix, dict):
            for items in matrix.values():
                if isinstance(items, list):
                    entries.extend(e for e in items if isinstance(e, dict))
        elif isinstance(matrix, list):
            entries = [e for e in matrix if isinstance(e, dict)]

        unflagged = [
            e["id"] for e in entries
            if e.get("id") in ready
            and not ready[e["id"]].get("official_docs")
            and not e.get("status")
        ]
        assert not unflagged, (
            f"Ready concepts missing official_docs with no status flag: {unflagged}"
        )

    def test_optional_links_have_value_or_note(self) -> None:
        """Every matrix entry should have skill_builder_links, lab_links,
        or an explanatory note — otherwise it looks uncurated."""
        matrix = _load_yaml(COVERAGE_FILE)
        if matrix is None:
            pytest.skip("Coverage matrix does not exist")

        entries: list[dict] = []
        if isinstance(matrix, dict):
            for items in matrix.values():
                if isinstance(items, list):
                    entries.extend(e for e in items if isinstance(e, dict))
        elif isinstance(matrix, list):
            entries = [e for e in matrix if isinstance(e, dict)]

        incomplete = [
            e["id"] for e in entries
            if not (e.get("skill_builder_links") or e.get("lab_links")
                    or e.get("note") or e.get("status") or e.get("flag"))
        ]
        assert not incomplete, (
            f"No optional links AND no explanatory note: {incomplete}"
        )
