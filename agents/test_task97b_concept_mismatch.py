"""Task 9.7b — Eval harness: concept ID mismatch detection.

AC3: Harness detects when Rex challenge concept_id differs from
     the selected concept's ID (Rex free-roamed).

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


# ---------------------------------------------------------------------------
# AC3 — Harness detects concept ID mismatch
# ---------------------------------------------------------------------------

class TestAC3_HarnessDetectsConceptMismatch:
    """Harness must detect when Rex challenge concept_id differs from selected concept."""

    def test_check_concept_id_match_returns_mismatch(self):
        """check_concept_id_match must return pass=False when IDs differ."""
        from agents.evals.checks import check_concept_id_match

        selected_concept = _fake_concept(id="deploy-codepipeline-basics")

        result = check_concept_id_match(
            challenge_topic="Lambda Basics",  # Rex free-roamed
            challenge_concept_id="lambda-runtime-config",  # Different concept
            selected_concept=selected_concept,
        )
        assert result.get("pass") is False, (
            f"Concept ID mismatch must be flagged. Got: {result}"
        )

    def test_check_concept_id_match_passes_when_ids_match(self):
        """check_concept_id_match must return pass=True when challenge and
        selected concept IDs are the same."""
        from agents.evals.checks import check_concept_id_match

        concept = _fake_concept()
        result = check_concept_id_match(
            challenge_topic=concept["topic"],
            challenge_concept_id=concept["id"],
            selected_concept=concept,
        )
        assert result.get("pass") is True, f"Matching concept IDs must pass. Got: {result}"
