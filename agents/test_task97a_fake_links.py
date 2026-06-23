"""Task 9.7a — Eval harness: fake/out-of-packet link detection (AC2).

AC2: Harness detects fake/out-of-packet links in Sage responses.

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
