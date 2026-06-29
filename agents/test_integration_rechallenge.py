"""Integration tests — rechallenge uses app-selected concept."""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

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


REQUIRES_INFRA = pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY") or not os.environ.get("DATABASE_URL"),
    reason=(
        "Integration test requires OPENROUTER_API_KEY and DATABASE_URL "
        "(Postgres + OpenRouter); skipped when either is unset."
    ),
)


@REQUIRES_INFRA
class TestConceptPacketInRechallenge:
    """Rechallenge uses select_rechallenge_concept, not topic_stats."""

    def test_rechallenge_node_calls_select_rechallenge_concept(self):
        """rex_rechallenge must import and call select_rechallenge_concept."""
        assert (_AGENTS_DIR / "nodes" / "rex_rechallenge.py").is_file()
        source = (_AGENTS_DIR / "nodes" / "rex_rechallenge.py").read_text()
        assert "select_rechallenge_concept" in source, (
            "rex_rechallenge.py must import select_rechallenge_concept from "
            "concepts.selector."
        )

    def test_rechallenge_selects_different_concept_id(self):
        """After rechallenge, current_concept_id must differ from the initial."""
        initial_concept = {
            "id": "deploy-codepipeline-basics",
            "domain": "Deployment",
            "task_statement": "Deploy via CI/CD.",
            "topic": "CodePipeline Basics",
            "topic_id": "deploy-codepipeline-basics",
            "task_statement_id": "deploy-codepipeline-basics",
            "services": ["CodePipeline"],
            "source_ids": [],
            "familiarity_level": "new",
            "ready": True,
        }
        rechallenge_concept = {
            "id": "deploy-cicd-services",
            "domain": "Deployment",
            "task_statement": "Use CI/CD services.",
            "topic": "CI/CD Services",
            "topic_id": "deploy-cicd-services",
            "task_statement_id": "deploy-cicd-services",
            "services": ["CodePipeline", "CodeBuild", "CodeDeploy"],
            "source_ids": [],
            "familiarity_level": "new",
            "ready": True,
        }

        from nodes import coach_open as coach_open_module
        from nodes import rex_rechallenge as rechallenge_module

        with patch.object(coach_open_module, "select_initial_concept", return_value=initial_concept):
            with patch.object(rechallenge_module, "select_rechallenge_concept", return_value=rechallenge_concept):
                state = _minimal_state()
                graph = _graph()

                state_after_coach = graph.invoke(state, node="coach_open")
                initial_cid = state_after_coach.get("current_concept_id")

                state_after_coach["current_challenge"] = {
                    "concept_id": initial_cid,
                    "domain": "Deployment",
                    "topic": state_after_coach.get("current_topic", "CodePipeline Basics"),
                    "topic_id": initial_cid,
                    "task_statement_id": initial_cid,
                    "task_statement": initial_concept["task_statement"],
                    "services": initial_concept["services"],
                    "source_ids": [],
                    "familiarity_level": "new",
                    "scenario": "Test.",
                    "question": "What?",
                    "difficulty": "medium",
                }

                state_after_rechallenge = graph.invoke(state_after_coach, node="rex_rechallenge")

        new_cid = state_after_rechallenge.get("current_concept_id")
        assert new_cid != initial_cid, (
            f"Rechallenge must change current_concept_id ({initial_cid!r} → {new_cid!r})"
        )

    def test_rechallenge_stays_in_same_domain(self):
        """Rechallenge concept must belong to the same domain as the initial."""
        initial_concept = {
            "id": "deploy-codepipeline-basics",
            "domain": "Deployment",
            "task_statement": "Deploy via CI/CD.",
            "topic": "CodePipeline Basics",
            "topic_id": "deploy-codepipeline-basics",
            "task_statement_id": "deploy-codepipeline-basics",
            "services": ["CodePipeline"],
            "source_ids": [],
            "familiarity_level": "new",
            "ready": True,
        }
        rechallenge_concept = {
            "id": "deploy-cicd-services",
            "domain": "Deployment",
            "task_statement": "Use CI/CD services.",
            "topic": "CI/CD Services",
            "topic_id": "deploy-cicd-services",
            "task_statement_id": "deploy-cicd-services",
            "services": ["CodePipeline"],
            "source_ids": [],
            "familiarity_level": "new",
            "ready": True,
        }

        from nodes import coach_open as coach_open_module
        from nodes import rex_rechallenge as rechallenge_module

        with patch.object(coach_open_module, "select_initial_concept", return_value=initial_concept):
            with patch.object(rechallenge_module, "select_rechallenge_concept", return_value=rechallenge_concept):
                state = _minimal_state()
                graph = _graph()

                state_after_coach = graph.invoke(state, node="coach_open")
                initial_domain = state_after_coach.get("current_domain")
                initial_cid = state_after_coach.get("current_concept_id", initial_concept["id"])

                state_after_coach["current_challenge"] = {
                    "concept_id": initial_cid,
                    "domain": initial_domain,
                    "topic": state_after_coach.get("current_topic", "CodePipeline Basics"),
                    "topic_id": initial_cid,
                    "task_statement_id": initial_cid,
                    "task_statement": initial_concept["task_statement"],
                    "services": initial_concept["services"],
                    "source_ids": [],
                    "familiarity_level": "new",
                    "scenario": "Test.",
                    "question": "What?",
                    "difficulty": "medium",
                }

                state_after_rechallenge = graph.invoke(state_after_coach, node="rex_rechallenge")

        assert state_after_rechallenge.get("current_domain") == initial_domain
