"""Integration tests — concept packet in challenge node."""
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
    """Seed state for a minimal session graph run."""
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


class TestConceptPacketInChallenge:
    """Verify concept selection and packet population through the graph."""

    def test_coach_open_sets_current_concept_id(self):
        """After coach_open, state must contain current_concept_id."""
        fake_concept = {
            "id": "deploy-codepipeline-basics",
            "domain": "Deployment",
            "task_statement": "Deploy via CI/CD.",
            "topic": "CodePipeline Basics",
            "topic_id": "deploy-codepipeline-basics",
            "task_statement_id": "deploy-codepipeline-basics",
            "services": ["CodePipeline", "CodeBuild"],
            "source_ids": ["sb-deploy-pipelines"],
            "familiarity_level": "new",
            "ready": True,
        }

        from nodes import coach_open as coach_open_module

        with patch.object(coach_open_module, "select_initial_concept", return_value=fake_concept):
            state = _minimal_state()
            graph = _graph()
            result = graph.invoke(state, node="coach_open")

        assert "current_concept_id" in result
        assert result["current_concept_id"] == fake_concept["id"]

    def test_current_concept_id_is_in_appstate_keys(self):
        """AppState TypedDict must declare current_concept_id."""
        state = _minimal_state()
        assert "current_concept_id" in state

    def test_rex_challenge_receives_concept_packet_fields(self):
        """rex_challenge must receive task_statement, services, source_ids
        from the concept selected by coach_open — not freeform generation."""
        fake_concept = {
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
        }

        from nodes import coach_open as coach_open_module

        with patch.object(coach_open_module, "select_initial_concept", return_value=fake_concept):
            state = _minimal_state()
            graph = _graph()

            state_after_coach = graph.invoke(state, node="coach_open")

            assert state_after_coach.get("current_task_statement") == fake_concept["task_statement"]
            assert state_after_coach.get("current_services") == fake_concept["services"]
            assert state_after_coach.get("current_source_ids") == fake_concept["source_ids"]
