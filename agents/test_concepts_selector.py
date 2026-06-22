"""Tests for agents/concepts/selector.py — closed-book concept selection.

These tests define the contract for task 9.3:
- select_initial_concept selects a ready concept (optionally scoped to a domain).
- select_rechallenge_concept selects a ready concept in the same domain,
  excluding the previous one, with priority: weak > uncovered > any.
- Both raise NoReadyConcept when no qualifying concept exists.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from concepts.loader import load_all_concepts
from concepts.schema import Concept

# These imports will fail until task 9.3 is implemented.
# They are the contractual entry points being tested.
from concepts.selector import NoReadyConcept, select_initial_concept, select_rechallenge_concept  # noqa: F401, E402


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def deployment_concepts():
    """All ready Deployment-domain concepts from dva-c02."""
    return [c for c in load_all_concepts("dva-c02") if c["domain"] == "Deployment"]


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
        # Validate via the existing Concept dataclass to confirm full shape.
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

        # Capture what load_all_concepts returns so we can seed on top of it.
        concepts_list = load_all_concepts("dva-c02")

        # Patch load_all_concepts so the selector uses a known stable list.
        monkeypatch.setattr("concepts.selector.load_all_concepts", lambda *a, **k: concepts_list)

        # Seed Python's random — the selector must use it.
        random.seed(42)
        first = select_initial_concept("dva-c02")

        random.seed(42)
        second = select_initial_concept("dva-c02")

        assert first["id"] == second["id"]


# ---------------------------------------------------------------------------
# TestSelectRechallengeConcept
# ---------------------------------------------------------------------------

class TestSelectRechallengeConcept:
    def test_returns_ready_concept_in_same_domain(self, deployment_concepts):
        assert len(deployment_concepts) >= 2, "Need at least 2 Deployment concepts"
        previous = deployment_concepts[0]
        result = select_rechallenge_concept(
            exam_id="dva-c02",
            domain="Deployment",
            previous_concept_id=previous["id"],
            user_id="test-user-rechallenge",
        )
        assert result.get("domain") == "Deployment"
        assert result.get("ready") is True

    def test_excludes_previous_concept_id(self, deployment_concepts):
        """Rechallenge must not return the same concept twice in a row."""
        previous = deployment_concepts[0]
        result = select_rechallenge_concept(
            exam_id="dva-c02",
            domain="Deployment",
            previous_concept_id=previous["id"],
            user_id="test-user-rechallenge",
        )
        assert result.get("id") != previous["id"]

    def test_weak_prioritised_over_uncovered(self, deployment_concepts, monkeypatch):
        """Concept with a prior incorrect exchange (weak) must be chosen over
        an uncovered concept (no prior exchange)."""
        if len(deployment_concepts) < 2:
            pytest.skip("Need at least 2 Deployment concepts for this test")

        concept_a = deployment_concepts[0]  # weak
        concept_b = deployment_concepts[1]  # uncovered

        # Patch the exchange-history lookup so concept_a looks weak
        # and concept_b looks uncovered.
        def fake_exchange_history(user_id: str, exam_id: str) -> list[dict]:
            return [
                {
                    "concept_id": concept_a["id"],
                    "outcome": "incorrect",
                }
            ]

        monkeypatch.setattr("concepts.selector.exchange_history_for_user", fake_exchange_history)
        monkeypatch.setattr("concepts.selector.load_all_concepts", lambda *a, **k: deployment_concepts)

        result = select_rechallenge_concept(
            exam_id="dva-c02",
            domain="Deployment",
            previous_concept_id=concept_a["id"],
            user_id="test-user",
        )
        # Should return the weak concept (concept_a) for re-drilling.
        assert result["id"] == concept_a["id"]

    def test_uncovered_prioritised_over_any(self, deployment_concepts, monkeypatch):
        """When no weak concept exists, the uncovered one (no prior exchange)
        must be chosen over a concept with a correct prior outcome."""
        if len(deployment_concepts) < 2:
            pytest.skip("Need at least 2 Deployment concepts for this test")

        concept_a = deployment_concepts[0]  # previously correct — not weak, not uncovered
        concept_b = deployment_concepts[1]  # uncovered

        def fake_exchange_history(user_id: str, exam_id: str) -> list[dict]:
            return [
                {
                    "concept_id": concept_a["id"],
                    "outcome": "correct",
                }
            ]

        monkeypatch.setattr("concepts.selector.exchange_history_for_user", fake_exchange_history)
        monkeypatch.setattr("concepts.selector.load_all_concepts", lambda *a, **k: deployment_concepts)

        result = select_rechallenge_concept(
            exam_id="dva-c02",
            domain="Deployment",
            previous_concept_id=concept_a["id"],
            user_id="test-user",
        )
        # Should return the uncovered concept_b.
        assert result["id"] == concept_b["id"]

    def test_falls_back_to_any_ready_when_no_weak_no_uncovered(
        self, deployment_concepts, monkeypatch
    ):
        """When all concepts in domain have correct prior outcomes,
        the selector falls back to any ready same-domain concept."""
        if len(deployment_concepts) < 2:
            pytest.skip("Need at least 2 Deployment concepts for this test")

        # Mark all concepts as correct (not weak, not uncovered).
        def fake_exchange_history(user_id: str, exam_id: str) -> list[dict]:
            return [
                {"concept_id": c["id"], "outcome": "correct"}
                for c in deployment_concepts
            ]

        monkeypatch.setattr("concepts.selector.exchange_history_for_user", fake_exchange_history)
        monkeypatch.setattr("concepts.selector.load_all_concepts", lambda *a, **k: deployment_concepts)

        previous = deployment_concepts[0]["id"]
        result = select_rechallenge_concept(
            exam_id="dva-c02",
            domain="Deployment",
            previous_concept_id=previous,
            user_id="test-user",
        )
        # Must be in same domain and not the previous concept.
        assert result["domain"] == "Deployment"
        assert result["id"] != previous
        assert result["ready"] is True

    def test_raises_NoReadyConcept_when_domain_has_no_ready_concepts(self):
        with pytest.raises(NoReadyConcept) as exc_info:
            select_rechallenge_concept(
                exam_id="dva-c02",
                domain="NonexistentDomain",
                previous_concept_id="any-id",
                user_id="test-user",
            )
        assert "NonexistentDomain" in str(exc_info.value)

    def test_raises_NoReadyConcept_when_only_concept_is_previous_concept_id(
        self, deployment_concepts, monkeypatch,
    ):
        """If only one ready concept exists in the domain and it's the
        previous_concept_id, there is no valid rechallenge target."""
        if len(deployment_concepts) < 1:
            pytest.skip("Need at least 1 Deployment concept for this test")

        only_concept = deployment_concepts[0]
        # Mock load_all_concepts to return a single-concept domain so this
        # mirrors the "only concept" edge case without relying on fixture size.
        monkeypatch.setattr("concepts.selector.load_all_concepts", lambda *a, **k: [only_concept])
        monkeypatch.setattr("concepts.selector.exchange_history_for_user", lambda *a, **k: [])

        with pytest.raises(NoReadyConcept):
            select_rechallenge_concept(
                exam_id="dva-c02",
                domain="Deployment",
                previous_concept_id=only_concept["id"],
                user_id="test-user",
            )


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
                user_id="any-user",
            )
