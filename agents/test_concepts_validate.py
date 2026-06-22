"""Tests for agents/concepts/validate.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from concepts.schema import Concept
from concepts.validate import ConceptValidation, validate_concept


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def valid_dict(**overrides) -> dict:
    base = {
        "id": "test-id",
        "domain": "Deployment",
        "task_statement": "Deploy via CI/CD pipelines.",
        "lesson_reference": "sb-deploy",
        "facts": ["F1 is true.", "F2 is true.", "F3 is true."],
        "traps": ["T1 is a common misconception."],
        "expected_answer_criteria": "Answer must mention CodePipeline.",
        "official_docs": ["https://docs.aws.amazon.com/codepipeline/latest/userguide/"],
        "skill_builder_links": [],
        "lab_links": [],
        "ready": True,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestValidateConcept_HappyPath:
    def test_valid_dict_returns_valid_true(self) -> None:
        result = validate_concept(valid_dict())
        assert result.valid is True
        assert result.errors == ()

    def test_valid_concept_object_returns_valid_true(self) -> None:
        c = Concept(
            id="test-id",
            domain="Deployment",
            task_statement="Deploy via CI/CD pipelines.",
            facts=["F1 is true.", "F2 is true.", "F3 is true."],
            traps=["T1 is a common misconception."],
            expected_answer_criteria="Answer must mention CodePipeline.",
            official_docs=["https://docs.aws.amazon.com/codepipeline/latest/userguide/"],
            ready=True,
        )
        result = validate_concept(c)
        assert result.valid is True
        assert result.errors == ()


# ---------------------------------------------------------------------------
# Required scalar fields
# ---------------------------------------------------------------------------

class TestValidateConcept_RequiredScalars:
    @pytest.mark.parametrize("field", ["id", "domain", "task_statement", "expected_answer_criteria"])
    def test_missing_required_scalar_fails(self, field: str) -> None:
        data = valid_dict()
        data[field] = ""
        result = validate_concept(data)
        assert result.valid is False
        assert any(field in e for e in result.errors)

    def test_whitespace_only_required_scalar_fails(self) -> None:
        result = validate_concept(valid_dict(id="   ", domain="   "))
        assert result.valid is False
        assert result.concept_id == ""


# ---------------------------------------------------------------------------
# Facts: 2–4 inclusive
# ---------------------------------------------------------------------------

class TestValidateConcept_Facts:
    @pytest.mark.parametrize("count", [0, 1])
    def test_too_few_facts_fails(self, count: int) -> None:
        result = validate_concept(valid_dict(facts=[f"F{i}" for i in range(count)]))
        assert result.valid is False
        assert any("facts must have 2" in e for e in result.errors)

    @pytest.mark.parametrize("count", [5, 6, 10])
    def test_too_many_facts_fails(self, count: int) -> None:
        result = validate_concept(valid_dict(facts=[f"F{i}" for i in range(count)]))
        assert result.valid is False
        assert any("facts must have 2" in e for e in result.errors)

    @pytest.mark.parametrize("count", [2, 3, 4])
    def test_exact_boundary_counts_pass(self, count: int) -> None:
        result = validate_concept(valid_dict(facts=[f"F{i}" for i in range(count)]))
        assert result.valid is True


# ---------------------------------------------------------------------------
# Traps: at least 1
# ---------------------------------------------------------------------------

class TestValidateConcept_Traps:
    def test_empty_traps_fails(self) -> None:
        result = validate_concept(valid_dict(traps=[]))
        assert result.valid is False
        assert any("traps must have at least 1" in e for e in result.errors)

    def test_single_trap_passes(self) -> None:
        result = validate_concept(valid_dict(traps=["Common misconception about IAM roles."]))
        assert result.valid is True


# ---------------------------------------------------------------------------
# Official docs URLs
# ---------------------------------------------------------------------------

class TestValidateConcept_OfficialDocs:
    def test_empty_official_docs_fails(self) -> None:
        result = validate_concept(valid_dict(official_docs=[]))
        assert result.valid is False
        assert any("official_docs must contain at least one" in e for e in result.errors)

    def test_non_url_string_fails(self) -> None:
        result = validate_concept(valid_dict(official_docs=["not-a-url"]))
        assert result.valid is False
        assert any("official_docs" in e and "URL" in e for e in result.errors)

    def test_http_url_passes(self) -> None:
        result = validate_concept(valid_dict(official_docs=["http://docs.aws.amazon.com"]))
        assert result.valid is True

    def test_https_url_passes(self) -> None:
        result = validate_concept(valid_dict(official_docs=["https://docs.aws.amazon.com"]))
        assert result.valid is True


# ---------------------------------------------------------------------------
# Error accumulation
# ---------------------------------------------------------------------------

class TestValidateConcept_ErrorAccumulation:
    def test_multiple_errors_all_collected(self) -> None:
        result = validate_concept(
            valid_dict(
                id="",
                facts=["only one"],
                traps=[],
                official_docs=[],
            )
        )
        assert result.valid is False
        assert len(result.errors) >= 4

    def test_concept_validation_dataclass_fields(self) -> None:
        result = validate_concept(valid_dict(id="my-concept"))
        assert isinstance(result, ConceptValidation)
        assert result.concept_id == "my-concept"
