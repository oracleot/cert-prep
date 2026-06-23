"""Task 9.4b — Evaluator grounded to expected_answer_criteria + traps.

AC2: Evaluator prompt receives expected_answer_criteria + traps;
     response includes missed_criteria + triggered_traps.

All tests compile and run; they fail until 9.4 is implemented.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from test_task93_shared import _node_graph, _seed_state, FakeLLM
from test_task94a_rex_grounding import _FAKE_CONCEPT  # noqa: F401

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


# ---------------------------------------------------------------------------
# AC2 — Evaluator receives expected_answer_criteria + traps; returns misses
# ---------------------------------------------------------------------------

class TestAC2_EvaluatorPromptIncludesCriteriaAndTraps:
    """Evaluator must receive expected_answer_criteria and traps in its prompt."""

    def test_evaluator_input_includes_criteria_and_traps(self):
        """EvaluatorInput dataclass must have expected_answer_criteria + traps."""
        from dataclasses import fields
        from prompts.evaluator import EvaluatorInput

        field_names = {f.name for f in fields(EvaluatorInput)}
        assert "expected_answer_criteria" in field_names
        assert "traps" in field_names

    def test_build_evaluator_prompt_includes_criteria(self):
        """build_evaluator_prompt must render expected_answer_criteria."""
        from prompts.evaluator import EvaluatorInput, build_evaluator_prompt

        ev = EvaluatorInput(
            exam_id="dva-c02",
            domain="Deployment",
            topic="CodePipeline Basics",
            scenario="An engineer configures a pipeline.",
            question="Which stage triggers a build?",
            user_answer="CodeBuild stage.",
            expected_answer_criteria=_FAKE_CONCEPT["expected_answer_criteria"],
            traps=_FAKE_CONCEPT["traps"],
        )
        system, user = build_evaluator_prompt(ev)
        assert _FAKE_CONCEPT["expected_answer_criteria"] in user

    def test_build_evaluator_prompt_includes_traps(self):
        """build_evaluator_prompt must render traps into the prompt."""
        from prompts.evaluator import EvaluatorInput, build_evaluator_prompt

        ev = EvaluatorInput(
            exam_id="dva-c02",
            domain="Deployment",
            topic="CodePipeline Basics",
            scenario="An engineer configures a pipeline.",
            question="Which stage triggers a build?",
            user_answer="CodeBuild stage.",
            expected_answer_criteria=_FAKE_CONCEPT["expected_answer_criteria"],
            traps=_FAKE_CONCEPT["traps"],
        )
        _, user = build_evaluator_prompt(ev)
        for trap in _FAKE_CONCEPT["traps"]:
            assert trap in user, f"Trap not in evaluator user prompt: {trap!r}"


class TestAC2_EvaluatorResponseIncludesMisses:
    """evaluate_answer node must extract missed_criteria and triggered_traps."""

    def test_evaluate_answer_returns_missed_criteria_and_triggered_traps(self):
        """evaluate_answer output must include missed_criteria + triggered_traps."""
        from nodes import coach_open as coach_open_module

        concept = dict(_FAKE_CONCEPT)
        with patch.object(coach_open_module, "select_initial_concept", return_value=concept):
            state = _seed_state()
            graph = _node_graph()
            state_after_coach = graph.invoke(state, node="coach_open")

            state_after_coach["current_challenge"] = {
                "concept_id": concept["id"],
                "domain": "Deployment",
                "topic": "CodePipeline Basics",
                "topic_id": concept["id"],
                "task_statement_id": concept["id"],
                "task_statement": concept["task_statement"],
                "services": concept["services"],
                "source_ids": concept["source_ids"],
                "familiarity_level": "new",
                "scenario": "Test scenario.",
                "question": "Which stage is required?",
                "expected_answer_criteria": concept["expected_answer_criteria"],
                "traps": concept["traps"],
            }

            with patch(
                "nodes.evaluate_answer.get_llm",
                return_value=FakeLLM(
                    '{"outcome":"incorrect",'
                    '"reasoning":"Answer did not mention CodePipeline stages."}'
                ),
            ):
                result = graph.invoke(state_after_coach, node="evaluate_answer")

        evaluation = result.get("last_evaluation", {})
        assert "missed_criteria" in evaluation
        assert "triggered_traps" in evaluation
        assert isinstance(evaluation["missed_criteria"], list)
        assert isinstance(evaluation["triggered_traps"], list)

    def test_evaluate_answer_handles_empty_criteria(self):
        """evaluate_answer must not crash when expected_answer_criteria is empty."""
        from nodes import coach_open as coach_open_module

        concept = dict(_FAKE_CONCEPT)
        with patch.object(coach_open_module, "select_initial_concept", return_value=concept):
            state = _seed_state()
            graph = _node_graph()
            state_after_coach = graph.invoke(state, node="coach_open")

            state_after_coach["current_challenge"] = {
                "concept_id": concept["id"],
                "domain": "Deployment",
                "topic": "CodePipeline Basics",
                "topic_id": concept["id"],
                "task_statement_id": concept["id"],
                "task_statement": concept["task_statement"],
                "services": concept["services"],
                "source_ids": concept["source_ids"],
                "familiarity_level": "new",
                "scenario": "Test.",
                "question": "What?",
                "expected_answer_criteria": "",
                "traps": concept["traps"],
            }

            with patch(
                "nodes.evaluate_answer.get_llm",
                return_value=FakeLLM('{"outcome":"correct","reasoning":"Correct."}'),
            ):
                result = graph.invoke(state_after_coach, node="evaluate_answer")

        assert "missed_criteria" in result.get("last_evaluation", {})
        assert "triggered_traps" in result.get("last_evaluation", {})
