"""Tests for agents/concepts/schema.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from concepts.schema import Concept


class TestConceptDataclass:
    """Concept dataclass has all required fields."""

    def test_required_scalar_fields_present(self) -> None:
        c = Concept(
            id="test-concept",
            domain="Deployment",
            task_statement="Deploy via CI/CD.",
            ready=True,
        )
        assert c.id == "test-concept"
        assert c.domain == "Deployment"
        assert c.task_statement == "Deploy via CI/CD."
        assert c.ready is True

    def test_defaults(self) -> None:
        c = Concept(id="x", domain="D", task_statement="T")
        assert c.facts == []
        assert c.traps == []
        assert c.expected_answer_criteria == ""
        assert c.official_docs == []
        assert c.skill_builder_links == []
        assert c.lab_links == []
        assert c.lesson_reference == ""
        assert c.ready is False

    def test_all_collection_fields_populated(self) -> None:
        c = Concept(
            id="all-fields",
            domain="Security",
            task_statement="Manage IAM access.",
            facts=["F1", "F2", "F3"],
            traps=["T1", "T2"],
            expected_answer_criteria="Correct answer references roles.",
            official_docs=["https://aws.example.com/docs"],
            skill_builder_links=["https://aws.example.com/sb"],
            lab_links=["https://aws.example.com/lab"],
            lesson_reference="sb-iam-roles",
            ready=True,
        )
        assert len(c.facts) == 3
        assert len(c.traps) == 2
        assert len(c.official_docs) == 1
        assert len(c.skill_builder_links) == 1
        assert len(c.lab_links) == 1

    def test_fact_count_property(self) -> None:
        c = Concept(id="x", domain="D", task_statement="T", facts=["a", "b", "c"])
        assert c.fact_count == 3

    def test_trap_count_property(self) -> None:
        c = Concept(id="x", domain="D", task_statement="T", traps=["t1"])
        assert c.trap_count == 1

    def test_official_docs_count_property(self) -> None:
        c = Concept(
            id="x",
            domain="D",
            task_statement="T",
            official_docs=["https://a.com", "https://b.com"],
        )
        assert c.official_docs_count == 2

    def test_frozen_dataclass(self) -> None:
        c = Concept(id="x", domain="D", task_statement="T")
        with pytest.raises(AttributeError):
            c.id = "y"  # type: ignore[assignment]
