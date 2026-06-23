"""Task 9.7a — Eval harness: resource-grounding checks.

AC1: Eval samples ready concepts across all domains.
AC2: Harness detects fake/out-of-packet links in Sage responses.

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
        "task_statement": "Deploy via CI/CD pipelines.",
        "topic": "CodePipeline Basics",
        "topic_id": "deploy-codepipeline-basics",
        "task_statement_id": "deploy-codepipeline-basics",
        "services": ["CodePipeline"],
        "source_ids": ["sb-deploy-pipelines"],
        "familiarity_level": "new",
        "ready": True,
        "facts": [
            "CodePipeline has at least three stages: Source, Build, Deploy.",
            "CodeBuild projects run in isolated build environments.",
        ],
        "traps": ["CodeBuild does NOT run inside a VPC by default."],
        "expected_answer_criteria": (
            "Answer must mention at least one CodePipeline stage type."
        ),
        "official_docs": ["https://docs.aws.amazon.com/codepipeline/latest/userguide/"],
        "skill_builder_links": ["https://skillbuilder.aws/labs/"],
        "lab_links": ["https://clouderlabs.example.com/codepipeline-lab"],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# AC1 — Eval samples ready concepts across all domains
# ---------------------------------------------------------------------------

class TestAC1_EvalSamplesReadyConcepts:
    """The eval harness must sample only concepts where ready=True."""

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


# ---------------------------------------------------------------------------
# AC2 — Harness detects fake/out-of-packet links
# ---------------------------------------------------------------------------

class TestAC2_HarnessDetectsFakeLinks:
    """The harness must fail when Sage cites URLs outside the concept packet."""

    def test_detects_fake_anthropic_url(self):
        """A non-existent Anthropic URL not in the packet must fail."""
        from agents.evals.checks import check_resource_grounding

        concept = _fake_concept()
        challenge = {"concept_id": concept["id"], "topic": concept["topic"]}
        fake_url = "https://docs.anthropic.com/en/docs/claude-code/nonexistent-page"
        sage_response = f"See {fake_url}"
        citations = [{"url": fake_url, "title": "Fake Anthropic page", "snippet_id": "x"}]

        result = check_resource_grounding(
            challenge=challenge,
            concept_record=concept,
            sage_response=sage_response,
            citations=citations,
        )
        assert result.get("pass") is False, f"Fake Anthropic URL must fail. Got: {result}"

    def test_detects_totally_fake_domain(self):
        """A URL from a random non-AWS domain must fail."""
        from agents.evals.checks import check_resource_grounding

        concept = _fake_concept()
        challenge = {"concept_id": concept["id"], "topic": concept["topic"]}
        fake_url = "https://random-blog.example.com/aws-tips"
        sage_response = f"See {fake_url}"
        citations = [{"url": fake_url, "title": "Random blog", "snippet_id": "x"}]

        result = check_resource_grounding(
            challenge=challenge,
            concept_record=concept,
            sage_response=sage_response,
            citations=citations,
        )
        assert result.get("pass") is False, f"Random domain URL must fail. Got: {result}"

    def test_detects_url_not_in_official_docs_or_skill_builder_or_lab(self):
        """A valid-looking AWS URL not in the concept's official_docs must fail."""
        from agents.evals.checks import check_resource_grounding

        concept = _fake_concept()
        challenge = {"concept_id": concept["id"], "topic": concept["topic"]}
        fake_aws_url = "https://docs.aws.amazon.com/lambda/latest/dg/welcome.html"
        sage_response = f"See {fake_aws_url}"
        citations = [{"url": fake_aws_url, "title": "Lambda docs", "snippet_id": "x"}]

        result = check_resource_grounding(
            challenge=challenge,
            concept_record=concept,
            sage_response=sage_response,
            citations=citations,
        )
        assert result.get("pass") is False, (
            f"URL not in concept packet must fail. Got: {result}"
        )
