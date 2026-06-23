"""Task 9.7c — Eval harness: miss tracking + citation gate.

AC4: Harness detects missing missed_criteria / triggered_traps in evaluator output.
AC5: Phase cannot close if any citation is not in the selected concept packet.

All tests compile and run; they fail until 9.7 is implemented.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_concept(**overrides) -> dict:
    base = {
        "id": "deploy-codepipeline-basics",
        "domain": "Deployment",
        "topic": "CodePipeline Basics",
        "official_docs": ["https://docs.aws.amazon.com/codepipeline/latest/userguide/"],
        "skill_builder_links": ["https://skillbuilder.aws/labs/"],
        "lab_links": ["https://clouderlabs.example.com/codepipeline-lab"],
    }
    base.update(overrides)
    return base


def _minimal_artifact_and_targets():
    artifact = {
        "domains": [{
            "name": "Deployment",
            "weight": 30,
            "topics": [{"id": "deploy-codepipeline-basics", "name": "CodePipeline Basics"}],
            "task_statements": [],
        }],
    }
    targets = [{
        "domain": "Deployment",
        "topic_id": "deploy-codepipeline-basics",
        "topic": "CodePipeline Basics",
        "task_statement": "Deploy via CI/CD.",
        "services": ["CodePipeline"],
        "source_ids": [],
    }]
    return artifact, targets


# ---------------------------------------------------------------------------
# AC4 — Harness detects missing missed_criteria / triggered_traps
# ---------------------------------------------------------------------------

class TestAC4_HarnessDetectsMissingMissTracking:
    """Harness must verify that evaluator output includes miss fields."""

    def test_check_evaluator_miss_tracking_exists(self):
        """agents.evals.checks must have check_evaluator_miss_tracking function."""
        from agents.evals import checks

        assert hasattr(checks, "check_evaluator_miss_tracking")

    def test_check_evaluator_miss_tracking_flags_missing_fields(self):
        """check_evaluator_miss_tracking must return pass=False when
        missed_criteria or triggered_traps are absent."""
        from agents.evals.checks import check_evaluator_miss_tracking

        concept = _fake_concept()
        evaluator_output = {
            "outcome": "incorrect",
            "reasoning": "Missed the VPC trap.",
            # missing missed_criteria and triggered_traps
        }

        result = check_evaluator_miss_tracking(
            evaluator_output=evaluator_output,
            concept_record=concept,
        )
        assert result.get("pass") is False, (
            f"Missing missed_criteria/triggered_traps must fail. Got: {result}"
        )

    def test_check_evaluator_miss_tracking_passes_when_present(self):
        """check_evaluator_miss_tracking must pass when both fields are present."""
        from agents.evals.checks import check_evaluator_miss_tracking

        concept = _fake_concept()
        evaluator_output = {
            "outcome": "incorrect",
            "reasoning": "Missed the VPC trap.",
            "missed_criteria": ["CodeBuild defaults to no VPC"],
            "triggered_traps": [
                "CodeBuild does NOT run inside a VPC by default."
            ],
        }

        result = check_evaluator_miss_tracking(
            evaluator_output=evaluator_output,
            concept_record=concept,
        )
        assert result.get("pass") is True, f"Present miss fields must pass. Got: {result}"


# ---------------------------------------------------------------------------
# AC5 — Phase cannot close if any citation is not in the selected packet
# ---------------------------------------------------------------------------

class TestAC5_CitationMustBeInPacket:
    """The full eval analyze() must fail overall_status when resource_grounding fails."""

    def test_analyze_fails_whole_run_when_resource_grounding_fails(self):
        """If any sample fails resource_grounding, overall_status must be 'fail'."""
        from agents.evals.checks import analyze

        artifact, targets = _minimal_artifact_and_targets()
        concept = _fake_concept()
        samples = [{
            "id": "deploy-codepipeline-basics#1",
            "target": targets[0],
            "challenge": {
                "concept_id": concept["id"],
                "domain": "Deployment",
                "topic": "CodePipeline Basics",
                "scenario": "An engineer configures a pipeline.",
                "question": "Which stage is required?",
            },
            "sage_response": "See https://totally-fake.example.com",
            "citations": [
                {"url": "https://totally-fake.example.com", "title": "Fake", "snippet_id": "x"},
            ],
        }]

        report = analyze(
            exam_id="dva-c02",
            artifact=artifact,
            targets=targets,
            samples=samples,
            artifact_shape_errors=[],
            partial=True,
        )

        assert report.get("overall_status") == "fail", (
            f"overall_status must be 'fail' when resource_grounding fails. "
            f"Got: {report.get('overall_status')}"
        )
        checks = report.get("checks", {})
        assert checks.get("resource_grounding") is False, (
            f"resource_grounding check must be False. Got: {checks}"
        )

    def test_analyze_passes_whole_run_when_all_citations_in_packet(self):
        """If every sample passes resource_grounding, overall_status must be 'pass'."""
        from agents.evals.checks import analyze

        artifact, targets = _minimal_artifact_and_targets()
        concept = _fake_concept()
        samples = [{
            "id": "deploy-codepipeline-basics#1",
            "target": targets[0],
            "challenge": {
                "concept_id": concept["id"],
                "domain": "Deployment",
                "topic": "CodePipeline Basics",
                "scenario": "An engineer configures a pipeline.",
                "question": "Which stage is required?",
            },
            "sage_response": (
                f"See {concept['official_docs'][0]} "
                f"and {concept['skill_builder_links'][0]}"
            ),
            "citations": [
                {"url": concept["official_docs"][0], "title": "CodePipeline docs", "snippet_id": "x"},
                {"url": concept["skill_builder_links"][0], "title": "Skill Builder", "snippet_id": "y"},
            ],
        }]

        report = analyze(
            exam_id="dva-c02",
            artifact=artifact,
            targets=targets,
            samples=samples,
            artifact_shape_errors=[],
            partial=True,
        )

        assert report.get("overall_status") == "pass", (
            f"overall_status must be 'pass' when all samples pass. Got: {report}"
        )
