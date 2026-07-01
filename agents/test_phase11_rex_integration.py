"""Phase 11 — integration tests for option-based Rex challenge/rechallenge.

These exercise the rex_challenge / rex_rechallenge nodes end-to-end via the
shared ``_node_graph`` fixture, with the LLM mocked to return an
option-based payload. We verify:
  - 4 labeled A/B/C/D options land on the Challenge.
  - response_mode round-trips from state.current_response_mode.
  - answer_key is parsed and normalized.
  - A malformed Rex payload (3 options, bad labels, wrong answer_key size)
    hard-fails.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from test_task93_shared import _node_graph, _seed_state, FakeLLM

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


_FAKE_CONCEPT = {
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
        "CodePipeline has at least three stages.",
        "CodeBuild projects run in isolated environments.",
        "Pipeline state persists between executions.",
        "CodePipeline integrates with CloudWatch Events.",
    ],
    "traps": [
        "You cannot roll back a CodePipeline execution.",
        "CodeBuild does NOT run inside a VPC by default.",
    ],
    "expected_answer_criteria": (
        "Answer must mention at least one CodePipeline stage type."
    ),
    "official_docs": ["https://docs.aws.amazon.com/codepipeline/"],
    "skill_builder_links": ["https://skillbuilder.aws/labs/"],
    "lab_links": ["https://clouderlabs.example.com/codepipeline-lab"],
}


def _single_response_payload() -> str:
    return json.dumps({
        "domain": "Deployment",
        "topic": "CodePipeline Basics",
        "scenario": "An engineer configures a pipeline with source, build, and deploy stages.",
        "question": "Which stage type triggers a build?",
        "response_mode": "single_response",
        "options": [
            {"label": "A", "text": "Source"},
            {"label": "B", "text": "Build"},
            {"label": "C", "text": "Deploy"},
            {"label": "D", "text": "Approve"},
        ],
        "answer_key": ["B"],
    })


def _multi_response_payload() -> str:
    return json.dumps({
        "domain": "Deployment",
        "topic": "CI/CD Services",
        "scenario": "An engineer selects AWS managed CI/CD services for a pipeline.",
        "question": "Which TWO services combine to run a managed CI/CD pipeline?",
        "response_mode": "multiple_response",
        "options": [
            {"label": "A", "text": "CodePipeline"},
            {"label": "B", "text": "CodeBuild"},
            {"label": "C", "text": "Lambda"},
            {"label": "D", "text": "S3"},
        ],
        "answer_key": ["A", "B"],
    })


class TestRexChallengeOptionBased:
    """rex_challenge parses option-based payloads and validates the shape."""

    def test_single_response_round_trips(self):
        from nodes import coach_open as coach_open_module
        concept = dict(_FAKE_CONCEPT)
        with patch.object(coach_open_module, "select_initial_concept", return_value=concept):
            state = _seed_state()
            graph = _node_graph()
            state_after_coach = graph.invoke(state, node="coach_open")
            state_after_coach["current_response_mode"] = "single_response"

            with patch("nodes.rex_challenge.get_llm", return_value=FakeLLM(_single_response_payload())):
                result = graph.invoke(state_after_coach, node="rex_challenge")

        ch = result["current_challenge"]
        assert ch["response_mode"] == "single_response"
        assert [o["label"] for o in ch["options"]] == ["A", "B", "C", "D"]
        assert all(o["text"] for o in ch["options"])
        assert ch["answer_key"] == ["B"]

    def test_multi_response_round_trips(self):
        from nodes import coach_open as coach_open_module
        concept = dict(_FAKE_CONCEPT)
        with patch.object(coach_open_module, "select_initial_concept", return_value=concept):
            state = _seed_state()
            graph = _node_graph()
            state_after_coach = graph.invoke(state, node="coach_open")
            state_after_coach["current_response_mode"] = "multiple_response"

            with patch("nodes.rex_challenge.get_llm", return_value=FakeLLM(_multi_response_payload())):
                result = graph.invoke(state_after_coach, node="rex_challenge")

        ch = result["current_challenge"]
        assert ch["response_mode"] == "multiple_response"
        assert ch["answer_key"] == ["A", "B"]

    def test_three_options_rejected(self):
        from nodes import coach_open as coach_open_module
        bad_payload = json.dumps({
            "domain": "Deployment",
            "topic": "CodePipeline Basics",
            "scenario": "Bad prompt.",
            "question": "?",
            "response_mode": "single_response",
            "options": [
                {"label": "A", "text": "x"},
                {"label": "B", "text": "y"},
                {"label": "C", "text": "z"},
            ],
            "answer_key": ["A"],
        })
        concept = dict(_FAKE_CONCEPT)
        with patch.object(coach_open_module, "select_initial_concept", return_value=concept):
            state = _seed_state()
            graph = _node_graph()
            state_after_coach = graph.invoke(state, node="coach_open")
            state_after_coach["current_response_mode"] = "single_response"

            with patch("nodes.rex_challenge.get_llm", return_value=FakeLLM(bad_payload)):
                with pytest.raises(ValueError, match="4 options"):
                    graph.invoke(state_after_coach, node="rex_challenge")

    def test_single_response_with_two_correct_labels_rejected(self):
        from nodes import coach_open as coach_open_module
        bad_payload = json.dumps({
            "domain": "Deployment",
            "topic": "CodePipeline Basics",
            "scenario": "Bad prompt.",
            "question": "?",
            "response_mode": "single_response",
            "options": [
                {"label": "A", "text": "x"},
                {"label": "B", "text": "y"},
                {"label": "C", "text": "z"},
                {"label": "D", "text": "w"},
            ],
            "answer_key": ["A", "B"],
        })
        concept = dict(_FAKE_CONCEPT)
        with patch.object(coach_open_module, "select_initial_concept", return_value=concept):
            state = _seed_state()
            graph = _node_graph()
            state_after_coach = graph.invoke(state, node="coach_open")
            state_after_coach["current_response_mode"] = "single_response"

            with patch("nodes.rex_challenge.get_llm", return_value=FakeLLM(bad_payload)):
                with pytest.raises(ValueError, match="single_response"):
                    graph.invoke(state_after_coach, node="rex_challenge")


class TestRexRechallengeOptionBased:
    """rex_rechallenge also returns option-based challenges."""

    def test_rechallenge_returns_option_based_challenge(self):
        from nodes import coach_open as coach_open_module
        from nodes import rex_rechallenge as rechallenge_module
        initial_concept = dict(_FAKE_CONCEPT)
        rechallenge_concept = dict(_FAKE_CONCEPT)
        rechallenge_concept["id"] = "deploy-cicd-services"
        rechallenge_concept["topic"] = "CI/CD Services"

        with patch.object(coach_open_module, "select_initial_concept", return_value=initial_concept):
            with patch.object(rechallenge_module, "select_rechallenge_concept", return_value=rechallenge_concept):
                state = _seed_state()
                graph = _node_graph()
                state_after_coach = graph.invoke(state, node="coach_open")
                state_after_coach["current_response_mode"] = "multiple_response"
                state_after_coach["current_challenge"] = {
                    "domain": "Deployment",
                    "topic": "CodePipeline Basics",
                    "topic_id": "deploy-codepipeline-basics",
                    "task_statement_id": "deploy-codepipeline-basics",
                    "task_statement": "Deploy via CI/CD pipelines.",
                    "services": ["CodePipeline"],
                    "source_ids": [],
                    "familiarity_level": "new",
                    "scenario": "Earlier challenge.",
                    "question": "Earlier?",
                    "difficulty": "medium",
                    "concept_id": "deploy-codepipeline-basics",
                }

                with patch("nodes.rex_rechallenge.get_llm", return_value=FakeLLM(_multi_response_payload())):
                    result = graph.invoke(state_after_coach, node="rex_rechallenge")

        ch = result["current_challenge"]
        assert ch["response_mode"] == "multiple_response"
        assert ch["answer_key"] == ["A", "B"]
        assert [o["label"] for o in ch["options"]] == ["A", "B", "C", "D"]