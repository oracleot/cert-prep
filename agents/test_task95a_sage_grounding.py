"""Task 9.5a — Sage grounded to concept packet.

AC1: Sage receives concept packet (facts, traps, links);
     cites only packet links.

All tests compile and run; they fail until 9.5 is implemented.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from test_task93_shared import _node_graph, _seed_state
from test_task95_shared import (
    FAKE_CONCEPT,
    FakeSageLLM,
    run_sage_depth_sync,
    seed_state_with_challenge,
)

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


# ---------------------------------------------------------------------------
# AC1 — Sage receives concept packet and cites only packet links
# ---------------------------------------------------------------------------

class TestAC1_SageReceivesConceptPacket:
    """sage_respond must receive facts, traps, and links from the concept packet."""

    def test_sage_sources_includes_concept_links(self):
        """load_sage_grounding must include official_docs/skill_builder/lab_links."""
        from sage_sources import load_sage_grounding

        grounding = load_sage_grounding(
            exam_id="dva-c02",
            topic_id="deploy-codepipeline-basics",
            topic="CodePipeline Basics",
            services=["CodePipeline"],
            source_ids=["sb-deploy-pipelines"],
            official_docs=FAKE_CONCEPT["official_docs"],
            skill_builder_links=FAKE_CONCEPT["skill_builder_links"],
            lab_links=FAKE_CONCEPT["lab_links"],
        )
        context = grounding["source_context"]
        assert FAKE_CONCEPT["official_docs"][0] in context
        assert FAKE_CONCEPT["skill_builder_links"][0] in context
        assert FAKE_CONCEPT["lab_links"][0] in context

    def test_sage_sources_omits_links_not_in_packet(self):
        """load_sage_grounding must NOT include URLs outside the concept packet."""
        from sage_sources import load_sage_grounding

        grounding = load_sage_grounding(
            exam_id="dva-c02",
            topic_id="deploy-codepipeline-basics",
            topic="CodePipeline Basics",
            services=["CodePipeline"],
            source_ids=["sb-deploy-pipelines"],
            official_docs=FAKE_CONCEPT["official_docs"],
            skill_builder_links=FAKE_CONCEPT["skill_builder_links"],
            lab_links=FAKE_CONCEPT["lab_links"],
        )
        context = grounding["source_context"]
        assert "https://fake-unverified-site.example.com" not in context

    def test_sage_sources_handles_empty_links(self):
        """load_sage_grounding must not crash with empty link lists."""
        from sage_sources import load_sage_grounding

        grounding = load_sage_grounding(
            exam_id="dva-c02",
            topic_id="deploy-codepipeline-basics",
            topic="CodePipeline Basics",
            services=["CodePipeline"],
            source_ids=["sb-deploy-pipelines"],
            official_docs=[],
            skill_builder_links=[],
            lab_links=[],
        )
        assert "source_context" in grounding
        assert isinstance(grounding["citations"], list)

    def test_sage_input_receives_concept_links(self):
        """SageInput dataclass must have fields for concept links."""
        from dataclasses import fields
        from prompts.sage import SageInput

        field_names = {f.name for f in fields(SageInput)}
        assert "official_docs" in field_names
        assert "skill_builder_links" in field_names
        assert "lab_links" in field_names

    def test_sage_prompt_omits_invented_links_directive(self):
        """build_sage_depth_prompt must instruct Sage not to invent links."""
        from prompts.sage import SageInput, build_sage_depth_prompt

        sage = SageInput(
            domain="Deployment",
            topic="CodePipeline Basics",
            scenario="An engineer configures a pipeline.",
            question="Which stage is required?",
            user_answer="Source stage.",
            reasoning="Correct.",
            source_context="Official docs: https://docs.aws.amazon.com/codepipeline/latest/userguide/",
            has_verified_sources=True,
            official_docs=["https://docs.aws.amazon.com/codepipeline/latest/userguide/"],
            skill_builder_links=["https://skillbuilder.aws/labs/"],
            lab_links=["https://clouderlabs.example.com/codepipeline-lab"],
        )
        _, user = build_sage_depth_prompt(sage)
        forbid_patterns = [
            r"do not invent",
            r"only cite",
            r"only use",
            r"invent|no invented",
        ]
        has_forbid = any(re.search(p, user, re.IGNORECASE) for p in forbid_patterns)
        assert has_forbid, f"Sage prompt must contain instruction against inventing citations.\nGot:\n{user[:500]}"

    def test_sage_respond_passes_links_to_sage_input(self):
        """sage_respond must extract links from current_challenge and pass to SageInput."""
        from nodes import coach_open as coach_open_module

        concept = dict(FAKE_CONCEPT)
        with patch.object(coach_open_module, "select_initial_concept", return_value=concept):
            state = _seed_state()
            graph = _node_graph()
            state_after_coach = graph.invoke(state, node="coach_open")

            state_after_coach.update({
                "current_challenge": {
                    "concept_id": concept["id"],
                    "domain": "Deployment",
                    "topic": "CodePipeline Basics",
                    "topic_id": concept["id"],
                    "task_statement_id": concept["id"],
                    "task_statement": concept["task_statement"],
                    "services": concept["services"],
                    "source_ids": concept["source_ids"],
                    "familiarity_level": "new",
                    "scenario": "Test.",
                    "question": "What?",
                    "expected_answer_criteria": concept["expected_answer_criteria"],
                    "traps": concept["traps"],
                    "official_docs": concept["official_docs"],
                    "skill_builder_links": concept["skill_builder_links"],
                    "lab_links": concept["lab_links"],
                },
                "user_answer": "Source stage.",
                "last_evaluation": {
                    "outcome": "correct",
                    "reasoning": "Correct.",
                    "answer_intent": "attempt",
                    "missed_criteria": [],
                    "triggered_traps": [],
                },
                "answer_intent": "attempt",
                "cycle": 1,
                "session_history": [],
            })

        fake_response = (
            "CodePipeline requires a Source stage. "
            "See https://docs.aws.amazon.com/codepipeline/latest/userguide/ "
            "and https://skillbuilder.aws/labs/"
        )
        import nodes.sage_respond as sage_module
        with patch.object(sage_module, "get_llm", return_value=FakeSageLLM(fake_response)):
            result = run_sage_depth_sync(sage_module, state_after_coach, fake_response)

        assert isinstance(result, dict)
        session_history = result.get("session_history", [])
        assert len(session_history) == 1
        exchange = session_history[0]
        # All citations must come from the concept packet.
        packet_urls = (
            concept["official_docs"]
            + concept["skill_builder_links"]
            + concept["lab_links"]
        )
        for citation in exchange.get("citations", []):
            url = citation["url"]
            assert url in packet_urls, f"Citation URL {url!r} not in concept packet"
