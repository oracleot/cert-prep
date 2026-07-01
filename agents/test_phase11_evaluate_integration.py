"""Phase 11 — evaluate_answer integration tests for option-based challenges."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from test_task93_shared import _node_graph, _seed_state, FakeLLM

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


def _seed_with_option_challenge(state: dict, mode: str, answer_key: list[str]) -> dict:
    """Seed the state with a fully-formed option-based challenge."""
    state["current_challenge"] = {
        "domain": "Deployment",
        "topic": "CodePipeline Basics",
        "topic_id": "deploy-codepipeline-basics",
        "task_statement_id": "deploy-codepipeline-basics",
        "task_statement": "Deploy via CI/CD pipelines.",
        "services": ["CodePipeline"],
        "source_ids": [],
        "familiarity_level": "new",
        "scenario": "An engineer configures a pipeline.",
        "question": "Which stage triggers a build?",
        "difficulty": "medium",
        "concept_id": "deploy-codepipeline-basics",
        "response_mode": mode,
        "options": [
            {"label": "A", "text": "Source"},
            {"label": "B", "text": "Build"},
            {"label": "C", "text": "Deploy"},
            {"label": "D", "text": "Approve"},
        ],
        "answer_key": answer_key,
    }
    return state


class TestEvaluateAnswerOptionBased:
    """evaluate_answer uses exact-match scoring when the challenge is option-based."""

    def test_single_response_correct(self):
        state = _seed_state()
        _seed_with_option_challenge(state, "single_response", ["B"])
        state["selected_labels"] = ["B"]

        graph = _node_graph()
        result = graph.invoke(state, node="evaluate_answer")

        ev = result["last_evaluation"]
        assert ev["outcome"] == "correct"
        assert ev["selected_labels"] == ["B"]
        assert ev["correct_labels"] == ["B"]
        assert ev["missed_labels"] == []
        assert ev["incorrect_labels"] == []

    def test_single_response_incorrect(self):
        state = _seed_state()
        _seed_with_option_challenge(state, "single_response", ["B"])
        state["selected_labels"] = ["A"]

        graph = _node_graph()
        result = graph.invoke(state, node="evaluate_answer")

        ev = result["last_evaluation"]
        assert ev["outcome"] == "incorrect"
        assert ev["missed_labels"] == ["B"]
        assert ev["incorrect_labels"] == ["A"]

    def test_multi_response_partial_is_incorrect(self):
        state = _seed_state()
        _seed_with_option_challenge(state, "multiple_response", ["A", "B"])
        state["selected_labels"] = ["A"]

        graph = _node_graph()
        result = graph.invoke(state, node="evaluate_answer")

        ev = result["last_evaluation"]
        assert ev["outcome"] == "incorrect"
        assert ev["missed_labels"] == ["B"]
        assert ev["incorrect_labels"] == []

    def test_multi_response_extra_is_incorrect(self):
        state = _seed_state()
        _seed_with_option_challenge(state, "multiple_response", ["A", "B"])
        state["selected_labels"] = ["A", "B", "C"]

        graph = _node_graph()
        result = graph.invoke(state, node="evaluate_answer")

        ev = result["last_evaluation"]
        assert ev["outcome"] == "incorrect"
        assert ev["incorrect_labels"] == ["C"]

    def test_multi_response_exact_match_correct(self):
        state = _seed_state()
        _seed_with_option_challenge(state, "multiple_response", ["A", "B"])
        state["selected_labels"] = ["A", "B"]

        graph = _node_graph()
        result = graph.invoke(state, node="evaluate_answer")

        ev = result["last_evaluation"]
        assert ev["outcome"] == "correct"

    def test_user_answer_csv_fallback(self):
        """When selected_labels is empty, parser falls back to user_answer CSV."""
        state = _seed_state()
        _seed_with_option_challenge(state, "single_response", ["B"])
        state["user_answer"] = "B"
        # No selected_labels key — exercise the fallback path.

        graph = _node_graph()
        result = graph.invoke(state, node="evaluate_answer")

        ev = result["last_evaluation"]
        assert ev["outcome"] == "correct"

    def test_knowledge_gap_still_knowledge_gap(self):
        state = _seed_state()
        _seed_with_option_challenge(state, "single_response", ["B"])
        state["answer_intent"] = "knowledge_gap"

        graph = _node_graph()
        result = graph.invoke(state, node="evaluate_answer")

        ev = result["last_evaluation"]
        assert ev["outcome"] == "incorrect"
        assert ev["answer_intent"] == "knowledge_gap"
        assert ev["selected_labels"] == []