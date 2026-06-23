"""Task 9.7a — Eval harness: resource-grounding AC1 checks.

AC1: Eval harness includes resource_grounding check in analyze() output.

All tests compile and run; they fail until 9.7 is implemented.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from test_task97_shared import _fake_concept

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


# ---------------------------------------------------------------------------
# AC1 — Eval harness includes resource_grounding in analyze() output
# ---------------------------------------------------------------------------

class TestAC1_EvalSamplesReadyConcepts:
    """The eval harness must include resource_grounding check in analyze()."""

    def test_evals_module_has_resource_grounding_check(self):
        """agents/evals/checks.py must have check_resource_grounding function."""
        import agents.evals.checks as checks

        assert hasattr(checks, "check_resource_grounding")

    def test_resource_grounding_check_signature(self):
        """check_resource_grounding must accept challenge, concept_record,
        sage_response, and citations parameters."""
        import inspect
        from agents.evals.checks import check_resource_grounding

        sig = inspect.signature(check_resource_grounding)
        params = list(sig.parameters.keys())
        required = ["challenge", "concept_record", "sage_response", "citations"]
        for p in required:
            assert p in params, f"check_resource_grounding must have '{p}' parameter"

    def test_resource_grounding_check_returns_fake_link_failures(self):
        """check_resource_grounding must detect URLs not in the concept packet."""
        from agents.evals.checks import check_resource_grounding

        concept = _fake_concept()
        challenge = {"concept_id": concept["id"], "topic": concept["topic"]}
        sage_response = (
            "CodePipeline requires a Source stage. "
            "See https://docs.anthropic.com/fake-guide/ and "
            "https://totally-fake-site.example.com/no-such-page"
        )
        citations = [
            {"url": "https://docs.anthropic.com/fake-guide/", "title": "Fake Guide", "snippet_id": "x"},
            {"url": "https://totally-fake-site.example.com/no-such-page", "title": "Fake", "snippet_id": "y"},
        ]

        result = check_resource_grounding(
            challenge=challenge,
            concept_record=concept,
            sage_response=sage_response,
            citations=citations,
        )
        assert result.get("pass") is False, (
            f"check_resource_grounding must return pass=False for out-of-packet URLs. Got: {result}"
        )
        assert result.get("fake_link_failures") or result.get("out_of_packet_links")

    def test_resource_grounding_check_passes_with_packet_links_only(self):
        """check_resource_grounding must return pass=True when all citations
        are in the concept packet."""
        from agents.evals.checks import check_resource_grounding

        concept = _fake_concept()
        challenge = {"concept_id": concept["id"], "topic": concept["topic"]}
        sage_response = (
            "CodePipeline requires a Source stage. "
            "See https://docs.aws.amazon.com/codepipeline/latest/userguide/ "
            "and https://skillbuilder.aws/labs/"
        )
        citations = [
            {"url": concept["official_docs"][0], "title": "CodePipeline docs", "snippet_id": "x"},
            {"url": concept["skill_builder_links"][0], "title": "Skill Builder", "snippet_id": "y"},
        ]

        result = check_resource_grounding(
            challenge=challenge,
            concept_record=concept,
            sage_response=sage_response,
            citations=citations,
        )
        assert result.get("pass") is True, (
            f"check_resource_grounding must pass when all citations in packet. Got: {result}"
        )

    def test_evals_analyze_includes_resource_grounding_check(self):
        """agents.evals.analyze must include resource_grounding in its checks output."""
        from agents.evals.checks import analyze

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
                "Requires Source stage. "
                "See https://docs.aws.amazon.com/codepipeline/latest/userguide/"
            ),
            "citations": [
                {"url": "https://docs.aws.amazon.com/codepipeline/latest/userguide/",
                 "title": "Docs", "snippet_id": "x"},
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

        checks = report.get("checks", {})
        assert "resource_grounding" in checks, (
            f"analyze() checks must include 'resource_grounding'. Got: {list(checks.keys())}"
        )
