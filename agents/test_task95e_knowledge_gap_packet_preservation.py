"""Task 9.5e — knowledge-gap rechallenge preserves the full concept packet.

Regression for the Phase 9.5 blocker in agents/nodes/rex_rechallenge.py:
the ``answer_intent == 'knowledge_gap'`` branch rebuilt ``target`` from
``current_challenge`` (a Challenge TypedDict, which carries traps / links /
criteria but no ``facts``). ``concept_packet_fields(...)`` then cleared
``packet['facts']`` to ``[]`` and the returned ``current_concept_facts``
overwrote the previously good facts with ``[]`` — sending Rex an
ungrounded rechallenge prompt and stripping Sage of the concept's ground
truth for the next cycle.

This test asserts that facts / traps / expected_answer_criteria /
official_docs / skill_builder_links / lab_links all survive the
knowledge-gap rechallenge path and are forwarded into the new challenge
and onto state for downstream nodes.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

from test_task93_shared import _node_graph, _seed_state, FakeLLM
from test_task95_shared import FAKE_CONCEPT

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


# Standard challenge shape a Cycle-1 rex_challenge would have produced —
# carries traps / links / criteria but, like the Challenge TypedDict, no
# `facts` (facts live on state as `current_concept_facts`).
_CYCLE1_CHALLENGE = {
    "concept_id": FAKE_CONCEPT["id"],
    "domain": "Deployment",
    "topic": "CodePipeline Basics",
    "topic_id": FAKE_CONCEPT["id"],
    "task_statement_id": FAKE_CONCEPT["id"],
    "task_statement": FAKE_CONCEPT["task_statement"],
    "services": FAKE_CONCEPT["services"],
    "source_ids": FAKE_CONCEPT["source_ids"],
    "familiarity_level": "new",
    "scenario": "An engineer configures a pipeline.",
    "question": "Which stage is required?",
    "difficulty": "medium",
    "expected_answer_criteria": FAKE_CONCEPT["expected_answer_criteria"],
    "traps": FAKE_CONCEPT["traps"],
    "official_docs": FAKE_CONCEPT["official_docs"],
    "skill_builder_links": FAKE_CONCEPT["skill_builder_links"],
    "lab_links": FAKE_CONCEPT["lab_links"],
}

# What rex_rechallenge's LLM is expected to return for the new cycle.
_REX_RECHALLENGE_JSON = (
    '{"domain":"Deployment","topic":"CodePipeline Basics",'
    '"scenario":"An engineer must rebuild a failed deployment.",'
    '"question":"How do you re-run the failed stage?"}'
)


def _seed_knowledge_gap_state() -> dict:
    """State after a Cycle-1 knowledge-gap answer: coach_open has populated
    the packet fields on state, rex_challenge has populated current_challenge,
    evaluate_answer has set answer_intent='knowledge_gap'."""
    state = _seed_state()
    state.update({
        "current_concept_id": FAKE_CONCEPT["id"],
        "current_domain": "Deployment",
        "current_topic": FAKE_CONCEPT["topic"],
        "current_topic_id": FAKE_CONCEPT["id"],
        "current_task_statement_id": FAKE_CONCEPT["id"],
        "current_task_statement": FAKE_CONCEPT["task_statement"],
        "current_services": FAKE_CONCEPT["services"],
        "current_source_ids": FAKE_CONCEPT["source_ids"],
        "current_concept_facts": FAKE_CONCEPT["facts"],
        "current_concept_traps": FAKE_CONCEPT["traps"],
        "current_expected_answer_criteria": FAKE_CONCEPT["expected_answer_criteria"],
        "current_official_docs": FAKE_CONCEPT["official_docs"],
        "current_skill_builder_links": FAKE_CONCEPT["skill_builder_links"],
        "current_lab_links": FAKE_CONCEPT["lab_links"],
        "familiarity_level": "new",
        "rex_difficulty": "medium",
        "cycle": 1,
        "current_challenge": dict(_CYCLE1_CHALLENGE),
        "user_answer": "I don't know yet.",
        "last_evaluation": {
            "outcome": "incorrect",
            "reasoning": "Knowledge gap.",
            "answer_intent": "knowledge_gap",
            "missed_criteria": [],
            "triggered_traps": [],
        },
        "answer_intent": "knowledge_gap",
    })
    return state


# ---------------------------------------------------------------------------
# AC: knowledge-gap rechallenge preserves the full concept packet
# ---------------------------------------------------------------------------

class TestAC_KnowledgeGapRechallengePreservesPacket:
    """Knowledge-gap rechallenge must not clear concept facts / traps / links."""

    def test_state_packet_fields_survive_rechallenge(self):
        """All packet-derived state fields must survive knowledge-gap
        rechallenge: current_concept_facts, current_concept_traps,
        current_expected_answer_criteria, current_official_docs,
        current_skill_builder_links, current_lab_links.

        Pre-fix: target is built from current_challenge (Challenge TypedDict,
        no `facts`); concept_packet_fields clears packet['facts']=[]; the
        returned `current_concept_facts` overwrites the previously good
        facts with [] — sending Rex an ungrounded rechallenge prompt.
        Post-fix: target is seeded with state-level packet fields via
        setdefault, so the rechallenge keeps them and forwards them.
        """
        state = _seed_knowledge_gap_state()
        graph = _node_graph()

        with patch(
            "nodes.rex_rechallenge.get_llm",
            return_value=FakeLLM(_REX_RECHALLENGE_JSON),
        ):
            result = graph.invoke(state, node="rex_rechallenge")

        assert result.get("current_concept_facts") == FAKE_CONCEPT["facts"]
        assert result.get("current_concept_traps") == FAKE_CONCEPT["traps"]
        assert (
            result.get("current_expected_answer_criteria")
            == FAKE_CONCEPT["expected_answer_criteria"]
        )
        assert result.get("current_official_docs") == FAKE_CONCEPT["official_docs"]
        assert result.get("current_skill_builder_links") == FAKE_CONCEPT["skill_builder_links"]
        assert result.get("current_lab_links") == FAKE_CONCEPT["lab_links"]

    def test_new_challenge_carries_packet_resources(self):
        """The new current_challenge must carry traps / criteria / links so
        Sage and the persisted exchange record for cycle 2 stay grounded
        to the same concept Rex just used."""
        state = _seed_knowledge_gap_state()
        graph = _node_graph()

        with patch(
            "nodes.rex_rechallenge.get_llm",
            return_value=FakeLLM(_REX_RECHALLENGE_JSON),
        ):
            result = graph.invoke(state, node="rex_rechallenge")

        challenge = result.get("current_challenge", {})
        assert challenge.get("traps") == FAKE_CONCEPT["traps"]
        assert challenge.get("expected_answer_criteria") == FAKE_CONCEPT["expected_answer_criteria"]
        assert challenge.get("official_docs") == FAKE_CONCEPT["official_docs"]
        assert challenge.get("skill_builder_links") == FAKE_CONCEPT["skill_builder_links"]
        assert challenge.get("lab_links") == FAKE_CONCEPT["lab_links"]

    def test_knowledge_gap_rechallenge_does_not_skip_select_rechallenge_concept(self):
        """The fix is narrow: only the knowledge-gap path needs setdefault
        merging. The non-knowledge-gap path must still call
        select_rechallenge_concept (regression for the original Phase 9.3
        contract)."""
        from nodes import rex_rechallenge as rechallenge_module

        # When answer_intent != knowledge_gap, select_rechallenge_concept
        # must be called. Patching it to raise proves it was reached.
        def _boom(*a, **kw):
            raise AssertionError(
                "select_rechallenge_concept must be called on the "
                "non-knowledge-gap path"
            )

        state = _seed_knowledge_gap_state()
        state["answer_intent"] = "attempt"
        graph = _node_graph()

        with patch(
            "nodes.rex_rechallenge.get_llm",
            return_value=FakeLLM(_REX_RECHALLENGE_JSON),
        ):
            with patch.object(
                rechallenge_module,
                "select_rechallenge_concept",
                side_effect=_boom,
            ):
                # Should propagate the AssertionError because the path is hit.
                import pytest
                with pytest.raises(AssertionError):
                    graph.invoke(state, node="rex_rechallenge")