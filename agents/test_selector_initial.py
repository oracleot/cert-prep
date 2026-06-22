"""Tests for select_initial_concept and NoReadyConcept exception."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from test_concepts_shared import deployment_concepts

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from concepts.loader import load_all_concepts
from concepts.schema import Concept
from concepts.selector import NoReadyConcept, select_initial_concept, select_rechallenge_concept  # noqa: F401, E402


# ---------------------------------------------------------------------------
# TestSelectInitialConcept
# ---------------------------------------------------------------------------

class TestSelectInitialConcept:
    def test_returns_a_ready_concept(self):
        result = select_initial_concept("dva-c02")
        assert isinstance(result, dict)
        assert result.get("ready") is True
        assert isinstance(result.get("id"), str)
        assert isinstance(result.get("domain"), str)
        assert isinstance(result.get("task_statement"), str)

    def test_returns_a_concept_that_passes_schema(self):
        result = select_initial_concept("dva-c02")
        c = Concept(**{k: v for k, v in result.items() if k in Concept.__dataclass_fields__})
        assert c.ready is True

    def test_respects_domain_filter(self):
        result = select_initial_concept("dva-c02", domain="Deployment")
        assert result.get("domain") == "Deployment"

    def test_respects_security_domain_filter(self):
        result = select_initial_concept("dva-c02", domain="Security")
        assert result.get("domain") == "Security"

    def test_excludes_not_ready_concepts(self):
        """invalid-not-ready.yaml has ready=false; it must never be returned."""
        result = select_initial_concept("dva-c02")
        assert result.get("id") != "invalid-not-ready"

    def test_raises_NoReadyConcept_when_no_ready_in_domain(self):
        with pytest.raises(NoReadyConcept) as exc_info:
            select_initial_concept("dva-c02", domain="NonexistentDomain")
        assert "NonexistentDomain" in str(exc_info.value)

    def test_raises_NoReadyConcept_for_unknown_exam(self):
        with pytest.raises(NoReadyConcept):
            select_initial_concept("unknown-exam-xyz")

    def test_selection_is_deterministic_given_seed(self, monkeypatch):
        """Two calls with the same random seed return the same concept."""
        import random
        import concepts.selector

        concepts_list = load_all_concepts("dva-c02")
        monkeypatch.setattr("concepts.selector.load_all_concepts", lambda *a, **k: concepts_list)

        random.seed(42)
        first = select_initial_concept("dva-c02")

        random.seed(42)
        second = select_initial_concept("dva-c02")

        assert first["id"] == second["id"]


# ---------------------------------------------------------------------------
# TestNoReadyConcept
# ---------------------------------------------------------------------------

class TestNoReadyConcept:
    def test_exception_carries_domain_name(self):
        exc = NoReadyConcept(domain="Deployment")
        assert "Deployment" in str(exc)

    def test_exception_carries_exam_id_when_provided(self):
        exc = NoReadyConcept(domain="Security", exam_id="dva-c02")
        msg = str(exc)
        assert "Security" in msg
        assert "dva-c02" in msg

    def test_exception_is_raised_by_select_initial_concept(self):
        with pytest.raises(NoReadyConcept):
            select_initial_concept("dva-c02", domain="ZetaClassDomain")

    def test_exception_is_raised_by_select_rechallenge_concept(self):
        with pytest.raises(NoReadyConcept):
            select_rechallenge_concept(
                exam_id="dva-c02",
                domain="ZetaClassDomain",
                previous_concept_id="any-id",
                history=[],
            )
