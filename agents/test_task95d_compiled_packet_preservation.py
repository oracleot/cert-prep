"""Task 9.4/9.5/9.6 regression — Phase 9 packet fields survive the
full compiled graph state machine from coach_open into rex_challenge
and the persisted Challenge TypedDict.

The compiled LangGraph runtime filters output keys against the
AppState schema; any key not declared is silently dropped. This test
proves the Phase 9 packet fields are kept end-to-end through the
NodeAwareGraph wrapper (the same path /api/session/start takes at
runtime), so the schema/initial_state additions in this fix actually
prevent silent drops.
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from unittest.mock import patch

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from state import initial_state


def _minimal_state(user_id: str = "") -> dict:
    return initial_state(
        user_id=user_id or f"test-user-{uuid.uuid4().hex[:8]}",
        exam_id="dva-c02",
        max_cycles=2,
    )


def _graph():
    """Return a NodeAwareGraph via get_session_graph()."""
    import nest_asyncio
    nest_asyncio.apply()

    import graphs.session as _gs
    os.environ.pop("DATABASE_URL", None)
    _gs._cached_graph = None

    import db as _db
    import asyncio as _asyncio
    _asyncio.run(_db.init_checkpointer())

    from graphs.session import get_session_graph
    return get_session_graph()


_FAKE_CONCEPT = {
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
    "facts": [
        "CodePipeline orchestrates source, build, test, and deploy stages.",
        "CodePipeline can ingest source from CodeCommit, S3, GitHub, or Bitbucket.",
    ],
    "traps": [
        "CodePipeline itself does not run build commands.",
    ],
    "expected_answer_criteria": "Reference CodeBuild, not CodePipeline directly.",
    "official_docs": ["https://docs.aws.amazon.com/codepipeline/latest/userguide/"],
    "skill_builder_links": ["https://skillbuilder.aws/labs/"],
    "lab_links": ["https://aws.amazon.com/getting-started/hands-on/set-up-continuous-deployment-pipeline/"],
}


_FAKE_REX_RESPONSE = (
    '{"domain":"Deployment","topic":"CodePipeline Basics",'
    '"scenario":"An engineer configures a pipeline.",'
    '"question":"Which stage triggers a build?",'
    '"response_mode":"single_response",'
    '"options":[{"label":"A","text":"src"},{"label":"B","text":"build"},'
    '{"label":"C","text":"deploy"},{"label":"D","text":"approve"}],'
    '"answer_key":["B"]}'
)


# ---------------------------------------------------------------------------
# Phase 9 packet fields survive the compiled graph
# ---------------------------------------------------------------------------

class TestCompiledGraphPreservesPacketFields:
    """Phase 9 packet fields must survive every node boundary."""

    def test_appstate_schema_declares_all_phase9_packet_fields(self):
        """AppState TypedDict must declare every Phase 9 packet field
        that coach_open returns; otherwise the compiled runtime drops them."""
        state = _minimal_state()
        phase9_fields = [
            "current_concept_facts",
            "current_concept_traps",
            "current_expected_answer_criteria",
            "current_official_docs",
            "current_skill_builder_links",
            "current_lab_links",
        ]
        missing = [f for f in phase9_fields if f not in state]
        assert not missing, (
            f"initial_state() must declare all Phase 9 packet fields: missing {missing}"
        )

    def test_coach_open_packet_fields_appear_in_state(self):
        """coach_open must return all Phase 9 packet fields into state."""
        from nodes import coach_open as coach_open_module

        with patch.object(coach_open_module, "select_initial_concept", return_value=_FAKE_CONCEPT):
            state = _minimal_state()
            graph = _graph()
            result = graph.invoke(state, node="coach_open")

        assert result.get("current_concept_facts") == _FAKE_CONCEPT["facts"]
        assert result.get("current_concept_traps") == _FAKE_CONCEPT["traps"]
        assert result.get("current_expected_answer_criteria") == _FAKE_CONCEPT["expected_answer_criteria"]
        assert result.get("current_official_docs") == _FAKE_CONCEPT["official_docs"]
        assert result.get("current_skill_builder_links") == _FAKE_CONCEPT["skill_builder_links"]
        assert result.get("current_lab_links") == _FAKE_CONCEPT["lab_links"]

    def test_rex_challenge_receives_full_packet_after_coach_open(self):
        """End-to-end: after coach_open, rex_challenge must read packet
        fields from state — proving the fields survive the node boundary
        in the full compiled graph."""
        from nodes import coach_open as coach_open_module
        from nodes.rex_challenge import get_llm as rex_get_llm

        class _FakeResponse:
            def __init__(self, content: str) -> None:
                self.content = content

        class _FakeLLM:
            def invoke(self, *a, **k):
                return _FakeResponse(_FAKE_REX_RESPONSE)

            async def ainvoke(self, *a, **k):
                return _FakeResponse(_FAKE_REX_RESPONSE)

        with patch.object(coach_open_module, "select_initial_concept", return_value=_FAKE_CONCEPT):
            state = _minimal_state()
            graph = _graph()
            state_after_coach = graph.invoke(state, node="coach_open")

            with patch.object(sys.modules["nodes.rex_challenge"], "get_llm", return_value=_FakeLLM()):
                result = graph.invoke(state_after_coach, node="rex_challenge")

        challenge = result.get("current_challenge", {})

        assert challenge.get("official_docs") == _FAKE_CONCEPT["official_docs"], (
            "official_docs must be forwarded from coach_open into Challenge via rex_challenge"
        )
        assert challenge.get("skill_builder_links") == _FAKE_CONCEPT["skill_builder_links"], (
            "skill_builder_links must be forwarded from coach_open into Challenge via rex_challenge"
        )
        assert challenge.get("lab_links") == _FAKE_CONCEPT["lab_links"], (
            "lab_links must be forwarded from coach_open into Challenge via rex_challenge"
        )
        assert challenge.get("expected_answer_criteria") == _FAKE_CONCEPT["expected_answer_criteria"], (
            "expected_answer_criteria must be forwarded from coach_open into Challenge via rex_challenge"
        )
        assert challenge.get("traps") == _FAKE_CONCEPT["traps"], (
            "traps must be forwarded from coach_open into Challenge via rex_challenge"
        )

        assert result.get("current_official_docs") == _FAKE_CONCEPT["official_docs"], (
            "current_official_docs must survive on state through rex_challenge"
        )
        assert result.get("current_skill_builder_links") == _FAKE_CONCEPT["skill_builder_links"], (
            "current_skill_builder_links must survive on state through rex_challenge"
        )
        assert result.get("current_lab_links") == _FAKE_CONCEPT["lab_links"], (
            "current_lab_links must survive on state through rex_challenge"
        )
