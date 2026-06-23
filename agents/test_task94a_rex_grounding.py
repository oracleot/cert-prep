"""Task 9.4a — Rex grounded to concept packet facts/traps.

AC1: Rex challenge receives facts/traps/concept_id; JSON output echoes concept_id.

All tests compile and run; they fail until 9.4 is implemented.
"""
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
# Shared fixture — also used by test_task94b
# ---------------------------------------------------------------------------

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
        "CodePipeline has at least three stages: Source, Build, Deploy.",
        "CodeBuild projects run in isolated build environments.",
        "Pipeline state persists across stages between executions.",
        "CodePipeline integrates with CloudWatch Events for state changes.",
    ],
    "traps": [
        "You cannot roll back a CodePipeline execution — you must rerun or start a new one.",
        "CodeBuild does NOT run inside a VPC by default; you must explicitly enable VPC mode.",
    ],
    "expected_answer_criteria": (
        "Answer must mention at least one CodePipeline stage type "
        "(Source, Build, Deploy) and note that CodeBuild defaults to no VPC."
    ),
    "official_docs": ["https://docs.aws.amazon.com/codepipeline/latest/userguide/"],
    "skill_builder_links": ["https://skillbuilder.aws/labs/"],
    "lab_links": ["https://clouderlabs.example.com/codepipeline-lab"],
}


# ---------------------------------------------------------------------------
# AC1 — Rex is grounded to facts/traps and echoes concept_id
# ---------------------------------------------------------------------------

class TestAC1_RexGroundedToFactsAndTraps:
    """Rex challenge generation must be constrained to the concept's facts/traps."""

    def test_rex_prompt_includes_facts(self):
        """build_rex_challenge_prompt must include the concept's facts."""
        from prompts.rex import build_rex_challenge_prompt

        system, user = build_rex_challenge_prompt(
            exam_id="dva-c02",
            domain="Deployment",
            topic="CodePipeline Basics",
            task_statement="Deploy via CI/CD pipelines.",
            services=["CodePipeline"],
            source_ids=["sb-deploy-pipelines"],
            concept_id="deploy-codepipeline-basics",
            facts=_FAKE_CONCEPT["facts"],
            traps=_FAKE_CONCEPT["traps"],
        )
        for fact in _FAKE_CONCEPT["facts"]:
            assert fact in user, f"Fact not in Rex user prompt: {fact!r}"

    def test_rex_prompt_includes_traps(self):
        """build_rex_challenge_prompt must include the concept's traps."""
        from prompts.rex import build_rex_challenge_prompt

        _, user = build_rex_challenge_prompt(
            exam_id="dva-c02",
            domain="Deployment",
            topic="CodePipeline Basics",
            concept_id="deploy-codepipeline-basics",
            facts=_FAKE_CONCEPT["facts"],
            traps=_FAKE_CONCEPT["traps"],
        )
        for trap in _FAKE_CONCEPT["traps"]:
            assert trap in user, f"Trap not in Rex user prompt: {trap!r}"

    def test_rex_node_accepts_facts_and_traps_kwargs(self):
        """build_rex_challenge_prompt must accept 'facts' and 'traps' params."""
        import inspect
        from prompts.rex import build_rex_challenge_prompt

        sig = inspect.signature(build_rex_challenge_prompt)
        assert "facts" in sig.parameters
        assert "traps" in sig.parameters

    def test_rex_challenge_json_echoes_concept_id(self):
        """rex_challenge must return current_challenge.concept_id matching input."""
        from nodes import coach_open as coach_open_module

        concept = dict(_FAKE_CONCEPT)
        concept["facts"] = _FAKE_CONCEPT["facts"]
        concept["traps"] = _FAKE_CONCEPT["traps"]

        with patch.object(coach_open_module, "select_initial_concept", return_value=concept):
            state = _seed_state()
            graph = _node_graph()
            state_after_coach = graph.invoke(state, node="coach_open")

            with patch(
                "nodes.rex_challenge.get_llm",
                return_value=FakeLLM(
                    '{"domain":"Deployment","topic":"CodePipeline Basics",'
                    '"scenario":"An engineer configures a pipeline with source, '
                    'build, and deploy stages.",'
                    '"question":"Which stage type is required for a '
                    'CodePipeline to trigger a build?"}'
                ),
            ):
                result = graph.invoke(state_after_coach, node="rex_challenge")

        challenge = result.get("current_challenge", {})
        assert challenge.get("concept_id") == concept["id"], (
            f"Rex challenge concept_id mismatch: expected {concept['id']!r}, "
            f"got {challenge.get('concept_id')!r}"
        )

    def test_rex_challenge_fails_if_topic_outside_packet(self):
        """Rex topic must match the selected concept, not free-roam."""
        from nodes import coach_open as coach_open_module

        concept = dict(_FAKE_CONCEPT)
        with patch.object(coach_open_module, "select_initial_concept", return_value=concept):
            state = _seed_state()
            graph = _node_graph()
            state_after_coach = graph.invoke(state, node="coach_open")

            with patch(
                "nodes.rex_challenge.get_llm",
                return_value=FakeLLM(
                    '{"domain":"Deployment","topic":"Lambda Power Tuning Feature",'
                    '"scenario":"An engineer tunes Lambda memory settings.",'
                    '"question":"Which setting controls Lambda duration billing?"}'
                ),
            ):
                result = graph.invoke(state_after_coach, node="rex_challenge")

        challenge = result.get("current_challenge", {})
        assert challenge.get("topic") == concept["topic"], (
            f"Rex topic must match concept ({concept['topic']!r}), "
            f"got {challenge.get('topic')!r}"
        )
