"""Tests for agents/concepts/loader.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from concepts.loader import CONCEPTS_DIR, filter_ready, find_concept, load_all_concepts


# ---------------------------------------------------------------------------
# CONCEPTS_DIR constant
# ---------------------------------------------------------------------------

class TestConceptsDirConstant:
    def test_concepts_dir_exists(self) -> None:
        assert CONCEPTS_DIR.is_dir(), f"Expected {CONCEPTS_DIR} to be a directory"

    def test_dva_c02_subdir_exists(self) -> None:
        assert (CONCEPTS_DIR / "dva-c02").is_dir()


# ---------------------------------------------------------------------------
# load_all_concepts
# ---------------------------------------------------------------------------

class TestLoadAllConcepts:
    def test_returns_list(self) -> None:
        result = load_all_concepts("dva-c02")
        assert isinstance(result, list)

    def test_all_returned_records_are_dicts(self) -> None:
        concepts = load_all_concepts("dva-c02")
        assert all(isinstance(c, dict) for c in concepts)

    def test_all_returned_records_have_id(self) -> None:
        concepts = load_all_concepts("dva-c02")
        assert all("id" in c for c in concepts), "Every loaded record must have an 'id' field"

    def test_excludes_invalid_records(self) -> None:
        """invalid-too-few-facts has 1 fact and should be excluded."""
        concepts = load_all_concepts("dva-c02")
        ids = {c["id"] for c in concepts}
        assert "invalid-too-few-facts" not in ids

    def test_excludes_invalid_no_official_docs(self) -> None:
        concepts = load_all_concepts("dva-c02")
        ids = {c["id"] for c in concepts}
        assert "invalid-no-official-docs" not in ids

    def test_excludes_invalid_no_traps(self) -> None:
        concepts = load_all_concepts("dva-c02")
        ids = {c["id"] for c in concepts}
        assert "invalid-no-traps" not in ids

    def test_excludes_not_ready_records(self) -> None:
        """invalid-not-ready has ready=false and should be excluded."""
        concepts = load_all_concepts("dva-c02")
        ids = {c["id"] for c in concepts}
        assert "invalid-not-ready" not in ids

    def test_includes_valid_ready_records(self) -> None:
        concepts = load_all_concepts("dva-c02")
        ids = {c["id"] for c in concepts}
        assert "deploy-codepipeline-basics" in ids
        assert "security-iam-role-basics" in ids

    def test_unknown_exam_id_raises_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_all_concepts("unknown-exam")


# ---------------------------------------------------------------------------
# find_concept
# ---------------------------------------------------------------------------

class TestFindConcept:
    def test_finds_existing_ready_concept(self) -> None:
        record = find_concept("dva-c02", "deploy-codepipeline-basics")
        assert record["id"] == "deploy-codepipeline-basics"
        assert record["domain"] == "Deployment"

    def test_missing_concept_raises_key_error(self) -> None:
        with pytest.raises(KeyError) as exc_info:
            find_concept("dva-c02", "does-not-exist")
        assert "does-not-exist" in str(exc_info.value)

    def test_not_ready_concept_raises_key_error(self) -> None:
        """invalid-not-ready exists on disk but is excluded from the index."""
        with pytest.raises(KeyError) as exc_info:
            find_concept("dva-c02", "invalid-not-ready")
        assert "invalid-not-ready" in str(exc_info.value)

    def test_unknown_exam_id_raises_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            find_concept("unknown-exam", "any-id")


# ---------------------------------------------------------------------------
# filter_ready
# ---------------------------------------------------------------------------

class TestFilterReady:
    def test_exclude_unready_true_removes_not_ready(self) -> None:
        records = [
            {"id": "a", "domain": "D", "ready": True},
            {"id": "b", "domain": "D", "ready": False},
            {"id": "c", "domain": "D", "ready": True},
        ]
        result = filter_ready(records, exclude_unready=True)
        ids = [r["id"] for r in result]
        assert "b" not in ids
        assert "a" in ids
        assert "c" in ids

    def test_exclude_unready_false_keeps_all(self) -> None:
        records = [
            {"id": "a", "domain": "D", "ready": True},
            {"id": "b", "domain": "D", "ready": False},
        ]
        result = filter_ready(records, exclude_unready=False)
        ids = [r["id"] for r in result]
        assert "a" in ids
        assert "b" in ids

    def test_filter_by_domain(self) -> None:
        records = [
            {"id": "a", "domain": "Deployment", "ready": True},
            {"id": "b", "domain": "Security", "ready": True},
            {"id": "c", "domain": "Deployment", "ready": True},
        ]
        result = filter_ready(records, domain="Deployment")
        domains = [r["domain"] for r in result]
        assert all(d == "Deployment" for d in domains)
        assert len(result) == 2

    def test_filter_by_domain_excludes_mismatches(self) -> None:
        records = [
            {"id": "a", "domain": "Deployment", "ready": True},
            {"id": "b", "domain": "Security", "ready": True},
        ]
        result = filter_ready(records, domain="Security")
        ids = [r["id"] for r in result]
        assert "a" not in ids
        assert "b" in ids

    def test_filter_preserves_order(self) -> None:
        records = [
            {"id": "x", "domain": "Deployment", "ready": True},
            {"id": "y", "domain": "Deployment", "ready": True},
            {"id": "z", "domain": "Deployment", "ready": True},
        ]
        result = filter_ready(records)
        ids = [r["id"] for r in result]
        assert ids == ["x", "y", "z"]

    def test_empty_input_returns_empty_list(self) -> None:
        result = filter_ready([])
        assert result == []


# ---------------------------------------------------------------------------
# Integration: loader used end-to-end
# ---------------------------------------------------------------------------

class TestLoaderEndToEnd:
    def test_deployment_concepts_load_and_filter(self) -> None:
        all_concepts = load_all_concepts("dva-c02")
        deployment = filter_ready(all_concepts, domain="Deployment")
        assert all(c["domain"] == "Deployment" for c in deployment)

    def test_security_concepts_load_and_filter(self) -> None:
        all_concepts = load_all_concepts("dva-c02")
        security = filter_ready(all_concepts, domain="Security")
        assert all(c["domain"] == "Security" for c in security)
