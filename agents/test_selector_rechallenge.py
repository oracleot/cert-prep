"""Tests for select_rechallenge_concept — task 9.3 priority logic."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from test_concepts_shared import deployment_concepts

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from concepts.selector import NoReadyConcept, select_rechallenge_concept  # noqa: F401, E402


class TestSelectRechallengeConcept:
    def test_returns_ready_concept_in_same_domain(self, deployment_concepts):
        assert len(deployment_concepts) >= 2, "Need at least 2 Deployment concepts"
        previous = deployment_concepts[0]
        result = select_rechallenge_concept(
            exam_id="dva-c02",
            domain="Deployment",
            previous_concept_id=previous["id"],
            history=[],
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
            history=[],
        )
        assert result.get("id") != previous["id"]

    def test_weak_prioritised_over_uncovered(self, deployment_concepts, monkeypatch):
        """Concept with a prior incorrect exchange (weak) must be chosen over
        an uncovered concept (no prior exchange)."""
        if len(deployment_concepts) < 2:
            pytest.skip("Need at least 2 Deployment concepts for this test")

        concept_a = deployment_concepts[0]  # weak
        concept_b = deployment_concepts[1]  # uncovered

        def fake_history(exam_id: str, user_id: str) -> list[dict]:
            return [{"concept_id": concept_a["id"], "outcome": "incorrect"}]

        monkeypatch.setattr("concepts.selector.load_all_concepts", lambda *a, **k: deployment_concepts)

        result = select_rechallenge_concept(
            exam_id="dva-c02",
            domain="Deployment",
            previous_concept_id=concept_a["id"],
            history=fake_history("dva-c02", "test-user"),
        )
        assert result["id"] == concept_a["id"]

    def test_uncovered_prioritised_over_any(self, deployment_concepts, monkeypatch):
        """When no weak concept exists, the uncovered one must be chosen over
        a concept with a correct prior outcome."""
        if len(deployment_concepts) < 2:
            pytest.skip("Need at least 2 Deployment concepts for this test")

        concept_a = deployment_concepts[0]  # previously correct
        concept_b = deployment_concepts[1]  # uncovered

        def fake_history(exam_id: str, user_id: str) -> list[dict]:
            return [{"concept_id": concept_a["id"], "outcome": "correct"}]

        monkeypatch.setattr("concepts.selector.load_all_concepts", lambda *a, **k: deployment_concepts)

        result = select_rechallenge_concept(
            exam_id="dva-c02",
            domain="Deployment",
            previous_concept_id=concept_a["id"],
            history=fake_history("dva-c02", "test-user"),
        )
        assert result["id"] == concept_b["id"]

    def test_falls_back_to_any_ready_when_no_weak_no_uncovered(
        self, deployment_concepts, monkeypatch
    ):
        """When all concepts have correct outcomes, selector falls back to any
        ready same-domain concept."""
        if len(deployment_concepts) < 2:
            pytest.skip("Need at least 2 Deployment concepts for this test")

        def fake_history(exam_id: str, user_id: str) -> list[dict]:
            return [{"concept_id": c["id"], "outcome": "correct"} for c in deployment_concepts]

        monkeypatch.setattr("concepts.selector.load_all_concepts", lambda *a, **k: deployment_concepts)

        previous = deployment_concepts[0]["id"]
        result = select_rechallenge_concept(
            exam_id="dva-c02",
            domain="Deployment",
            previous_concept_id=previous,
            history=fake_history("dva-c02", "test-user"),
        )
        assert result["domain"] == "Deployment"
        assert result["id"] != previous
        assert result["ready"] is True

    def test_raises_NoReadyConcept_when_domain_has_no_ready_concepts(self):
        with pytest.raises(NoReadyConcept) as exc_info:
            select_rechallenge_concept(
                exam_id="dva-c02",
                domain="NonexistentDomain",
                previous_concept_id="any-id",
                history=[],
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
        monkeypatch.setattr("concepts.selector.load_all_concepts", lambda *a, **k: [only_concept])

        with pytest.raises(NoReadyConcept):
            select_rechallenge_concept(
                exam_id="dva-c02",
                domain="Deployment",
                previous_concept_id=only_concept["id"],
                history=[],
            )
