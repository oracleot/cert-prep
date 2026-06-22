"""Task 9.3 AC1 + AC2/AC3 — concept selection before Rex, challenge output."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from test_task93_shared import _node_graph, _seed_state, FakeLLM

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


# ---------------------------------------------------------------------------
# AC1 — session selects conceptId before Rex runs
# ---------------------------------------------------------------------------

class TestAC1_SessionSelectsConceptId:
    """App/session code selects conceptId before Rex runs."""

    def test_initial_state_declares_concept_fields(self):
        """All concept fields must be declared in initial_state()."""
        state = _seed_state()
        required_fields = [
            "current_concept_id", "current_topic", "current_task_statement",
            "current_services", "current_source_ids", "familiarity_level", "rex_difficulty",
        ]
        missing = [f for f in required_fields if f not in state]
        assert not missing, f"initial_state() is missing concept fields: {missing}"

    def test_coach_open_stamps_concept_id_into_state(self):
        """coach_open must return current_concept_id in state dict."""
        fake_concept = {
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
        }

        from nodes import coach_open as coach_open_module

        with patch.object(coach_open_module, "select_initial_concept", return_value=fake_concept):
            state = _seed_state()
            graph = _node_graph()
            result = graph.invoke(state, node="coach_open")

        assert "current_concept_id" in result
        assert result["current_concept_id"] == "deploy-codepipeline-basics"

    def test_coach_open_stamps_task_statement_and_services(self):
        """coach_open must propagate task_statement, services, source_ids to state."""
        fake_concept = {
            "id": "deploy-codepipeline-basics",
            "domain": "Deployment",
            "task_statement": "Deploy application updates using CI/CD pipelines.",
            "topic": "CodePipeline Basics",
            "topic_id": "deploy-codepipeline-basics",
            "task_statement_id": "deploy-codepipeline-basics",
            "services": ["CodePipeline", "CodeBuild"],
            "source_ids": ["sb-deploy-pipelines"],
            "familiarity_level": "new",
            "ready": True,
        }

        from nodes import coach_open as coach_open_module

        with patch.object(coach_open_module, "select_initial_concept", return_value=fake_concept):
            state = _seed_state()
            graph = _node_graph()
            result = graph.invoke(state, node="coach_open")

        assert result.get("current_task_statement") == "Deploy application updates using CI/CD pipelines."
        assert result.get("current_services") == ["CodePipeline", "CodeBuild"]
        assert result.get("current_source_ids") == ["sb-deploy-pipelines"]
        assert result.get("familiarity_level") == "new"


# ---------------------------------------------------------------------------
# AC2 — Rex receives concept packet, no free-roam
# AC3 — challenge output stores conceptId, domain, topic, task statement, source IDs
# ---------------------------------------------------------------------------

class TestAC2_AC3_ChallengeOutputConceptFields:
    """Challenge dict must include conceptId, domain, topic, task_statement, source IDs."""

    def test_rex_challenge_output_carries_concept_id(self):
        """rex_challenge must return current_challenge.concept_id from state."""
        fake_concept = {
            "id": "deploy-codepipeline-basics",
            "domain": "Deployment",
            "task_statement": "Deploy via CI/CD.",
            "topic": "CodePipeline Basics",
            "topic_id": "deploy-codepipeline-basics",
            "task_statement_id": "deploy-codepipeline-basics",
            "services": ["CodePipeline"],
            "source_ids": ["sb-deploy-pipelines"],
            "familiarity_level": "new",
            "ready": True,
        }

        from nodes import coach_open as coach_open_module

        with patch.object(coach_open_module, "select_initial_concept", return_value=fake_concept):
            state = _seed_state()
            graph = _node_graph()
            state_after_coach = graph.invoke(state, node="coach_open")

            with patch("nodes.rex_challenge.get_llm", return_value=FakeLLM(
                '{"domain":"Deployment","topic":"CodePipeline Basics","scenario":"Test scenario.","question":"What?"}'
            )):
                result = graph.invoke(state_after_coach, node="rex_challenge")

        challenge = result.get("current_challenge", {})
        assert "concept_id" in challenge
        assert challenge.get("concept_id") == "deploy-codepipeline-basics"

    def test_rex_challenge_output_includes_domain_topic_task_statement(self):
        """Challenge must carry domain, topic, task_statement, services, source_ids."""
        fake_concept = {
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
        }

        from nodes import coach_open as coach_open_module

        with patch.object(coach_open_module, "select_initial_concept", return_value=fake_concept):
            state = _seed_state()
            graph = _node_graph()
            state_after_coach = graph.invoke(state, node="coach_open")

            with patch("nodes.rex_challenge.get_llm", return_value=FakeLLM(
                '{"domain":"Deployment","topic":"CodePipeline Basics","scenario":"Test scenario.","question":"What?"}'
            )):
                result = graph.invoke(state_after_coach, node="rex_challenge")

        challenge = result.get("current_challenge", {})
        assert challenge.get("domain") == "Deployment"
        assert challenge.get("task_statement") == "Deploy via CI/CD pipelines."
        assert challenge.get("services") == ["CodePipeline", "CodeBuild"]
        assert challenge.get("source_ids") == ["sb-deploy-pipelines"]
