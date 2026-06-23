"""Task 9.6a — Exchange carries missed_criteria and triggered_traps.

AC1: Exchange TypedDict and sage_respond output include miss fields.

All tests compile and run; they fail until 9.6 is implemented.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from test_task93_shared import _node_graph, _seed_state

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


# ---------------------------------------------------------------------------
# Shared fixture — also used by 96b
# ---------------------------------------------------------------------------

FAKE_CONCEPT = {
    "id": "deploy-codepipeline-basics",
    "domain": "Deployment",
    "task_statement": "Deploy via CI/CD pipelines.",
    "topic": "CodePipeline Basics",
    "topic_id": "deploy-codepipeline-basics",
    "task_statement_id": "deploy-codepipeline-basics",
    "services": ["CodePipeline", "CodeBuild"],
    "source_ids": ["sb-deploy-pipelines"],
    "familiarity_level": "new",
    "ready": True,
    "facts": [
        "CodePipeline has at least three stages: Source, Build, Deploy.",
        "CodeBuild projects run in isolated build environments.",
    ],
    "traps": [
        "CodeBuild does NOT run inside a VPC by default; "
        "you must explicitly enable VPC mode.",
    ],
    "expected_answer_criteria": (
        "Answer must mention at least one CodePipeline stage type "
        "and note that CodeBuild defaults to no VPC."
    ),
    "official_docs": ["https://docs.aws.amazon.com/codepipeline/latest/userguide/"],
    "skill_builder_links": [],
    "lab_links": [],
}


# ---------------------------------------------------------------------------
# AC1 — Exchange carries missed_criteria and triggered_traps
# ---------------------------------------------------------------------------

class TestAC1_ExchangeCarriesMissedCriteriaAndTriggers:
    """Exchange TypedDict and sage_respond output must include miss fields."""

    def test_exchange_typeddict_has_missed_criteria(self):
        """Exchange TypedDict in state.py must declare missed_criteria field."""
        from state import Exchange

        hints = getattr(Exchange, "__annotations__", {})
        assert "missed_criteria" in hints, (
            "Exchange TypedDict must have 'missed_criteria' annotation"
        )

    def test_exchange_typeddict_has_triggered_traps(self):
        """Exchange TypedDict in state.py must declare triggered_traps field."""
        from state import Exchange

        hints = getattr(Exchange, "__annotations__", {})
        assert "triggered_traps" in hints, (
            "Exchange TypedDict must have 'triggered_traps' annotation"
        )

    def test_sage_respond_build_exchange_includes_miss_fields(self):
        """_build_exchange must extract missed_criteria and triggered_traps."""
        import nodes.sage_respond as sage_module

        state = _seed_state()
        state.update({
            "current_challenge": {
                "concept_id": FAKE_CONCEPT["id"],
                "domain": "Deployment",
                "topic": "CodePipeline Basics",
                "topic_id": FAKE_CONCEPT["id"],
                "task_statement_id": FAKE_CONCEPT["id"],
                "task_statement": FAKE_CONCEPT["task_statement"],
                "services": FAKE_CONCEPT["services"],
                "source_ids": FAKE_CONCEPT["source_ids"],
                "familiarity_level": "new",
                "scenario": "An engineer configures a pipeline.",
                "question": "Which stage is required?",
                "expected_answer_criteria": FAKE_CONCEPT["expected_answer_criteria"],
                "traps": FAKE_CONCEPT["traps"],
                "official_docs": FAKE_CONCEPT["official_docs"],
                "skill_builder_links": FAKE_CONCEPT["skill_builder_links"],
                "lab_links": FAKE_CONCEPT["lab_links"],
            },
            "user_answer": "Source stage.",
            "last_evaluation": {
                "outcome": "incorrect",
                "reasoning": "Answer mentioned Source but missed the VPC trap.",
                "answer_intent": "attempt",
                "missed_criteria": ["CodeBuild defaults to no VPC"],
                "triggered_traps": [
                    "CodeBuild does NOT run inside a VPC by default; "
                    "you must explicitly enable VPC mode."
                ],
            },
            "answer_intent": "attempt",
            "cycle": 1,
            "session_history": [],
            "db_session_id": "",
        })

        exchange = sage_module._build_exchange(
            state,
            sage_text="The VPC point is important — CodeBuild defaults to no VPC.",
            citations=[],
        )

        assert "missed_criteria" in exchange
        assert "triggered_traps" in exchange
        assert isinstance(exchange["missed_criteria"], list)
        assert isinstance(exchange["triggered_traps"], list)

    def test_missed_criteria_and_triggered_traps_are_correct_values(self):
        """Missed criteria/traps from evaluation must flow through to exchange."""
        import nodes.sage_respond as sage_module

        state = _seed_state()
        state.update({
            "current_challenge": {
                "concept_id": FAKE_CONCEPT["id"],
                "domain": "Deployment",
                "topic": "CodePipeline Basics",
                "topic_id": FAKE_CONCEPT["id"],
                "task_statement_id": FAKE_CONCEPT["id"],
                "task_statement": FAKE_CONCEPT["task_statement"],
                "services": FAKE_CONCEPT["services"],
                "source_ids": FAKE_CONCEPT["source_ids"],
                "familiarity_level": "new",
                "scenario": "Test.",
                "question": "What?",
                "expected_answer_criteria": FAKE_CONCEPT["expected_answer_criteria"],
                "traps": FAKE_CONCEPT["traps"],
                "official_docs": FAKE_CONCEPT["official_docs"],
                "skill_builder_links": FAKE_CONCEPT["skill_builder_links"],
                "lab_links": FAKE_CONCEPT["lab_links"],
            },
            "user_answer": "Source stage.",
            "last_evaluation": {
                "outcome": "incorrect",
                "reasoning": "Missed VPC.",
                "answer_intent": "attempt",
                "missed_criteria": ["CodeBuild defaults to no VPC"],
                "triggered_traps": [
                    "CodeBuild does NOT run inside a VPC by default; "
                    "you must explicitly enable VPC mode."
                ],
            },
            "answer_intent": "attempt",
            "cycle": 1,
            "session_history": [],
            "db_session_id": "",
        })

        exchange = sage_module._build_exchange(
            state,
            sage_text="CodeBuild does not run in a VPC by default.",
            citations=[],
        )

        assert "CodeBuild defaults to no VPC" in exchange["missed_criteria"]
        assert any(
            "VPC" in trap for trap in exchange["triggered_traps"]
        ), f"triggered_traps must contain VPC trap, got {exchange['triggered_traps']!r}"

    def test_correct_answer_has_empty_miss_fields(self):
        """When outcome is 'correct', missed_criteria and triggered_traps are empty."""
        import nodes.sage_respond as sage_module

        state = _seed_state()
        state.update({
            "current_challenge": {
                "concept_id": FAKE_CONCEPT["id"],
                "domain": "Deployment",
                "topic": "CodePipeline Basics",
                "topic_id": FAKE_CONCEPT["id"],
                "task_statement_id": FAKE_CONCEPT["id"],
                "task_statement": FAKE_CONCEPT["task_statement"],
                "services": FAKE_CONCEPT["services"],
                "source_ids": FAKE_CONCEPT["source_ids"],
                "familiarity_level": "new",
                "scenario": "Test.",
                "question": "What?",
                "expected_answer_criteria": FAKE_CONCEPT["expected_answer_criteria"],
                "traps": FAKE_CONCEPT["traps"],
                "official_docs": FAKE_CONCEPT["official_docs"],
                "skill_builder_links": FAKE_CONCEPT["skill_builder_links"],
                "lab_links": FAKE_CONCEPT["lab_links"],
            },
            "user_answer": "Source stage.",
            "last_evaluation": {
                "outcome": "correct",
                "reasoning": "Correct.",
                "answer_intent": "attempt",
                "missed_criteria": [],
                "triggered_traps": [],
            },
            "answer_intent": "attempt",
            "cycle": 1,
            "session_history": [],
            "db_session_id": "",
        })

        exchange = sage_module._build_exchange(
            state,
            sage_text="Correct — CodePipeline requires a Source stage.",
            citations=[],
        )
        assert exchange["missed_criteria"] == []
        assert exchange["triggered_traps"] == []
