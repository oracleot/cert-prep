"""Task 9.3 AC4 — rechallenge uses app-selected concept + edge cases."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from test_task93_shared import _node_graph, _seed_state, FakeLLM

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from concepts.selector import NoReadyConcept, select_rechallenge_concept


# ---------------------------------------------------------------------------
# AC4 — rechallenge uses app-selected weak/uncovered/related concept, no free-roam
# ---------------------------------------------------------------------------

class TestAC4_RechallengeUsesAppSelectedConcept:
    """Rechallenge must call select_rechallenge_concept, not free-roam."""

    def test_rex_rechallenge_node_calls_select_rechallenge_concept(self):
        """rex_rechallenge.py must import and call select_rechallenge_concept."""
        source = (_AGENTS_DIR / "nodes" / "rex_rechallenge.py").read_text()
        assert "select_rechallenge_concept" in source, (
            "rex_rechallenge.py must import select_rechallenge_concept from "
            "concepts.selector — not free-roam with topic_stats or hardcoded logic."
        )

    def test_rechallenge_returns_different_concept_id(self):
        """After rechallenge, current_concept_id must differ from initial."""
        initial_concept = {
            "id": "deploy-codepipeline-basics",
            "domain": "Deployment",
            "task_statement": "Deploy via CI/CD.",
            "topic": "CodePipeline Basics",
            "topic_id": "deploy-codepipeline-basics",
            "task_statement_id": "deploy-codepipeline-basics",
            "services": ["CodePipeline"],
            "source_ids": [],
            "familiarity_level": "new",
            "ready": True,
        }
        rechallenge_concept = {
            "id": "deploy-cicd-services",
            "domain": "Deployment",
            "task_statement": "Use CI/CD services.",
            "topic": "CI/CD Services",
            "topic_id": "deploy-cicd-services",
            "task_statement_id": "deploy-cicd-services",
            "services": ["CodePipeline", "CodeBuild", "CodeDeploy"],
            "source_ids": [],
            "familiarity_level": "new",
            "ready": True,
        }

        from nodes import coach_open as coach_open_module
        from nodes import rex_rechallenge as rechallenge_module

        with patch.object(coach_open_module, "select_initial_concept", return_value=initial_concept):
            with patch.object(rechallenge_module, "select_rechallenge_concept", return_value=rechallenge_concept):
                state = _seed_state()
                graph = _node_graph()
                state_after_coach = graph.invoke(state, node="coach_open")

                state_after_coach["current_challenge"] = {
                    "domain": "Deployment",
                    "topic": "CodePipeline Basics",
                    "topic_id": "deploy-codepipeline-basics",
                    "task_statement_id": "deploy-codepipeline-basics",
                    "task_statement": "Deploy via CI/CD.",
                    "services": ["CodePipeline"],
                    "source_ids": [],
                    "familiarity_level": "new",
                    "scenario": "Test.",
                    "question": "What?",
                    "difficulty": "medium",
                    "concept_id": initial_concept["id"],
                }

                with patch("nodes.rex_rechallenge.get_llm", return_value=FakeLLM(
                    '{"domain":"Deployment","topic":"CI/CD Services","scenario":"Test scenario.","question":"What?"}'
                )):
                    result = graph.invoke(state_after_coach, node="rex_rechallenge")

        new_cid = result.get("current_concept_id")
        assert new_cid != "deploy-codepipeline-basics", (
            f"Rechallenge must change current_concept_id; got {new_cid!r}"
        )
        assert result.get("current_domain") == "Deployment"

    def test_rechallenge_output_carries_new_concept_packet(self):
        """After rechallenge, the new concept's task_statement/services/source_ids
        must be reflected in the challenge output."""
        initial_concept = {
            "id": "deploy-codepipeline-basics",
            "domain": "Deployment",
            "task_statement": "Deploy via CI/CD.",
            "topic": "CodePipeline Basics",
            "topic_id": "deploy-codepipeline-basics",
            "task_statement_id": "deploy-codepipeline-basics",
            "services": ["CodePipeline"],
            "source_ids": [],
            "familiarity_level": "new",
            "ready": True,
        }
        rechallenge_concept = {
            "id": "deploy-cicd-services",
            "domain": "Deployment",
            "task_statement": "Use CI/CD services: CodePipeline, CodeBuild, CodeDeploy.",
            "topic": "CI/CD Services",
            "topic_id": "deploy-cicd-services",
            "task_statement_id": "deploy-cicd-services",
            "services": ["CodePipeline", "CodeBuild", "CodeDeploy"],
            "source_ids": ["sb-cicd-services"],
            "familiarity_level": "new",
            "ready": True,
        }

        from nodes import coach_open as coach_open_module
        from nodes import rex_rechallenge as rechallenge_module

        with patch.object(coach_open_module, "select_initial_concept", return_value=initial_concept):
            with patch.object(rechallenge_module, "select_rechallenge_concept", return_value=rechallenge_concept):
                state = _seed_state()
                graph = _node_graph()
                state_after_coach = graph.invoke(state, node="coach_open")
                state_after_coach["current_challenge"] = {
                    "domain": "Deployment",
                    "topic": "CodePipeline Basics",
                    "topic_id": "deploy-codepipeline-basics",
                    "task_statement_id": "deploy-codepipeline-basics",
                    "task_statement": "Deploy via CI/CD.",
                    "services": ["CodePipeline"],
                    "source_ids": [],
                    "familiarity_level": "new",
                    "scenario": "Test.",
                    "question": "What?",
                    "difficulty": "medium",
                    "concept_id": initial_concept["id"],
                }

                with patch("nodes.rex_rechallenge.get_llm", return_value=FakeLLM(
                    '{"domain":"Deployment","topic":"CI/CD Services","scenario":"Test scenario.","question":"What?"}'
                )):
                    result = graph.invoke(state_after_coach, node="rex_rechallenge")

        challenge = result.get("current_challenge", {})
        assert challenge.get("concept_id") == "deploy-cicd-services"
        assert challenge.get("task_statement") == "Use CI/CD services: CodePipeline, CodeBuild, CodeDeploy."
        assert challenge.get("services") == ["CodePipeline", "CodeBuild", "CodeDeploy"]
        assert challenge.get("source_ids") == ["sb-cicd-services"]


# ---------------------------------------------------------------------------
# AC4 edge case — select_rechallenge_concept edge cases
# ---------------------------------------------------------------------------

class TestAC4_SelectRechallengeEdgeCases:
    """Edge cases for select_rechallenge_concept."""

    def test_empty_domain_string_raises_no_ready_concept(self):
        """Passing empty string domain must raise NoReadyConcept, not crash."""
        with pytest.raises(NoReadyConcept):
            select_rechallenge_concept(
                exam_id="dva-c02",
                domain="",
                previous_concept_id="any-id",
                history=[],
            )

    def test_nonexistent_domain_raises_no_ready_concept(self):
        """Unknown domain must raise NoReadyConcept with the domain name."""
        with pytest.raises(NoReadyConcept) as exc_info:
            select_rechallenge_concept(
                exam_id="dva-c02",
                domain="ZetaClassDomain",
                previous_concept_id="any-id",
                history=[],
            )
        assert "ZetaClassDomain" in str(exc_info.value)
