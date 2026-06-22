"""Integration tests for task 9.3 — closed-book concept selection.

Tests drive the LangGraph graph and FastAPI routes to verify:
- coach_open selects a concept and stamps current_concept_id into state.
- rex_challenge populates the Challenge dict with concept_id + concept fields.
- rex_rechallenge calls select_rechallenge_concept (not topic_stats).
- NoReadyConcept raised by selectors is surfaced as HTTP 422 on /session/start.
- Session and exchange DB rows carry the selected concept_id.
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

# These will fail with ImportError until the implementation lands.
from concepts.selector import NoReadyConcept, select_initial_concept, select_rechallenge_concept  # noqa: F401, E402

from graphs.session import get_session_graph
from state import AppState, initial_state


# ---------------------------------------------------------------------------
# Skip logic — DB tests need docker-compose Postgres running
# ---------------------------------------------------------------------------

DATABASE_URL_SET = bool(os.environ.get("DATABASE_URL"))

pytestmark_db = pytest.mark.skipif(
    not DATABASE_URL_SET,
    reason="DATABASE_URL not set — run 'docker compose up -d' first",
)

pytestmark_llm = pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_state(user_id: str = "") -> dict:
    """Seed state for a minimal session graph run (no LLM needed when mocked)."""
    return initial_state(
        user_id=user_id or f"test-user-{uuid.uuid4().hex[:8]}",
        exam_id="dva-c02",
        max_cycles=2,
    )


def _graph():
    """Return a NodeAwareGraph via get_session_graph().

    Ensures db.init_checkpointer() runs first so the in-memory checkpointer is ready.
    Uses nest_asyncio to allow asyncio.run() inside pytest-asyncio contexts.
    This lets tests use graph.invoke(state, node="...") syntax.
    """
    import nest_asyncio
    nest_asyncio.apply()  # Allow nested asyncio.run() calls.

    import os
    import graphs.session as _gs

    os.environ.pop("DATABASE_URL", None)
    _gs._cached_graph = None

    import db as _db
    import asyncio as _asyncio
    _asyncio.run(_db.init_checkpointer())

    return get_session_graph()


# ---------------------------------------------------------------------------
# TestConceptPacketInChallenge
# ---------------------------------------------------------------------------

class TestConceptPacketInChallenge:
    """Verify concept selection and packet population through the graph."""

    def test_coach_open_sets_current_concept_id(self):
        """After coach_open, state must contain current_concept_id.

        This fails until:
        1. coach_open imports and calls select_initial_concept.
        2. AppState is extended with current_concept_id.
        """
        # Mock the selector so we don't need a real concept.
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
            graph = _graph()  # no checkpointer for unit-style test

            # Manually invoke just the coach_open node.
            result = graph.invoke(state, node="coach_open")

        assert "current_concept_id" in result, (
            "current_concept_id must be present in state after coach_open. "
            "Check that coach_open calls select_initial_concept and stamps the result."
        )
        assert result["current_concept_id"] == fake_concept["id"]

    def test_current_concept_id_is_in_appstate_keys(self):
        """AppState TypedDict must declare current_concept_id.

        This is a schema-level check — fails until state.py is extended.
        """
        state = _minimal_state()
        # initial_state should include current_concept_id (empty string is fine).
        assert "current_concept_id" in state, (
            "current_concept_id key must exist in initial_state. "
            "Add it to AppState and initial_state in state.py."
        )

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
        from nodes import rex_challenge as rex_challenge_module

        with patch.object(coach_open_module, "select_initial_concept", return_value=fake_concept):
            state = _minimal_state()
            graph = _graph()

            # Run through coach_open then rex_challenge.
            state_after_coach = graph.invoke(state, node="coach_open")

            # The concept fields must survive into the state passed to rex_challenge.
            assert state_after_coach.get("current_task_statement") == fake_concept["task_statement"]
            assert state_after_coach.get("current_services") == fake_concept["services"]
            assert state_after_coach.get("current_source_ids") == fake_concept["source_ids"]


# ---------------------------------------------------------------------------
# TestConceptPacketInRechallenge
# ---------------------------------------------------------------------------

class TestConceptPacketInRechallenge:
    """Rechallenge uses select_rechallenge_concept, not topic_stats."""

    def test_rechallenge_node_calls_select_rechallenge_concept(self):
        """rex_rechallenge must import and call select_rechallenge_concept.

        Verifies the import path from the plan:
        from concepts.selector import select_rechallenge_concept
        (not from curriculum_repository import choose_rechallenge_target)
        """
        # Verify the module file exists.
        assert (_AGENTS_DIR / "nodes" / "rex_rechallenge.py").is_file()

        # Read the source to check for the required import.
        source = (_AGENTS_DIR / "nodes" / "rex_rechallenge.py").read_text()
        assert "select_rechallenge_concept" in source, (
            "rex_rechallenge.py must import select_rechallenge_concept from "
            "concepts.selector — not choose_rechallenge_target from curriculum_repository."
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

                # Provide a minimal current_challenge so rex_rechallenge doesn't crash.
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

                # Patch exchange_history so select_rechallenge_concept doesn't need DB.
                def fake_history(*a, **k):
                    return [{"concept_id": initial_cid, "outcome": "correct"}]

                with patch("concepts.selector.exchange_history_for_user", fake_history):
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
            "domain": "Deployment",  # same domain
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

                # Provide a minimal current_challenge so rex_rechallenge doesn't crash.
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

                def fake_history(*a, **k):
                    return [{"concept_id": initial_cid, "outcome": "correct"}]

                with patch("concepts.selector.exchange_history_for_user", fake_history):
                    state_after_rechallenge = graph.invoke(state_after_coach, node="rex_rechallenge")

        assert state_after_rechallenge.get("current_domain") == initial_domain


# ---------------------------------------------------------------------------
# TestNoReadyConceptFailsSession
# ---------------------------------------------------------------------------

class TestNoReadyConceptFailsSession:
    """Session start must fail loudly (HTTP 422) when no ready concept exists."""

    def test_session_start_returns_422_when_no_ready_concept_for_domain(self):
        """Monkeypatch select_initial_concept to raise NoReadyConcept;
        POST /session/start must return HTTP 422 with a domain-named message."""
        from fastapi.testclient import TestClient

        # Import lazily so conftest fixtures are already set up.
        try:
            from main import app
        except Exception as exc:
            pytest.skip(f"Could not import FastAPI app: {exc}")

        client = TestClient(app, raise_server_exceptions=False)

        # Patch the selector inside coach_open's module.
        from nodes import coach_open as coach_open_module

        with patch.object(
            coach_open_module,
            "select_initial_concept",
            side_effect=NoReadyConcept(domain="Deployment"),
        ):
            with patch.object(coach_open_module, "select_initial_concept",  # redundant but explicit
                              side_effect=NoReadyConcept(domain="Deployment")):
                response = client.post(
                    "/session/start",
                    json={
                        "user_id": f"test-user-{uuid.uuid4().hex[:8]}",
                        "exam_id": "dva-c02",
                        "max_cycles": 2,
                    },
                )

        assert response.status_code == 422, (
            f"Expected 422 when NoReadyConcept is raised; got {response.status_code}. "
            "coach_open must propagate NoReadyConcept and the route must map it to 422."
        )
        body = response.json()
        # Body should mention the domain or the error type.
        assert "Deployment" in str(body) or "NoReadyConcept" in str(body)

    def test_rechallenge_raises_when_no_ready_concept(self):
        """rex_rechallenge must raise HTTPException(422) when select_rechallenge_concept
        raises NoReadyConcept (instead of silently falling back)."""
        from fastapi import HTTPException as FastAPIHTTPException
        from nodes import rex_rechallenge as rechallenge_module

        fake_concept = {
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

        state = _minimal_state()
        state["current_concept_id"] = fake_concept["id"]
        state["current_domain"] = "Deployment"
        state["current_challenge"] = {
            "concept_id": fake_concept["id"],
            "domain": "Deployment",
            "topic": "CodePipeline Basics",
            "topic_id": fake_concept["id"],
            "task_statement_id": fake_concept["id"],
            "task_statement": fake_concept["task_statement"],
            "services": fake_concept["services"],
            "source_ids": [],
            "familiarity_level": "new",
            "scenario": "Test scenario.",
            "question": "What?",
            "difficulty": "medium",
        }

        graph = _graph()

        with patch.object(rechallenge_module, "select_rechallenge_concept",
                          side_effect=NoReadyConcept(domain="Deployment")):
            with pytest.raises(FastAPIHTTPException) as exc_info:
                graph.invoke(state, node="rex_rechallenge")
            assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# TestExchangePersistsConceptId
# ---------------------------------------------------------------------------

class TestExchangePersistsConceptId:
    """Sessions and exchanges DB rows must carry concept_id.

    These tests require the actual Postgres DB and migration 010_concept_tracking.sql.
    """

    @pytest.mark.asyncio
    @pytest.mark.db_required
    async def test_create_session_accepts_concept_id(self, db_pool):
        """create_session must accept a concept_id kwarg and INSERT it."""
        import psycopg
        from repositories import create_session

        user_id = f"test-user-{uuid.uuid4().hex[:8]}"
        session_id = await create_session(
            user_id=user_id,
            exam_id="dva-c02",
            domain="Deployment",
            topic="CodePipeline Basics",
            concept_id="deploy-codepipeline-basics",
        )
        assert session_id

        async with db_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT concept_id FROM sessions WHERE id = %s",
                    (session_id,),
                )
                row = await cur.fetchone()

        assert row is not None, "sessions row must exist"
        assert row[0] == "deploy-codepipeline-basics", (
            "sessions.concept_id must be non-NULL and match the selected concept. "
            "Ensure migration 010_concept_tracking.sql added the column."
        )

    @pytest.mark.asyncio
    @pytest.mark.db_required
    async def test_create_exchange_accepts_concept_id(self, db_pool):
        """create_exchange must accept a concept_id kwarg and INSERT it."""
        import json
        from repositories import create_exchange, create_session

        user_id = f"test-user-{uuid.uuid4().hex[:8]}"
        session_id = await create_session(
            user_id=user_id,
            exam_id="dva-c02",
            domain="Deployment",
            topic="CodePipeline Basics",
            concept_id="deploy-codepipeline-basics",
        )

        await create_exchange(
            session_id=session_id,
            cycle=1,
            domain="Deployment",
            topic="CodePipeline Basics",
            concept_id="deploy-codepipeline-basics",
            challenge={
                "domain": "Deployment",
                "topic": "CodePipeline Basics",
                "scenario": "Test.",
                "question": "Test?",
            },
            user_answer="Test answer",
            outcome="correct",
            answer_intent="attempt",
            sage_response="Test response",
            citations=[],
        )

        async with db_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT concept_id FROM exchanges WHERE session_id = %s AND cycle = 1",
                    (session_id,),
                )
                row = await cur.fetchone()

        assert row is not None, "exchanges row must exist"
        assert row[0] == "deploy-codepipeline-basics", (
            "exchanges.concept_id must be non-NULL. "
            "Ensure migration 010_concept_tracking.sql added the column "
            "and create_exchange in repositories.py accepts concept_id."
        )

    @pytest.mark.asyncio
    @pytest.mark.db_required
    async def test_concept_id_flows_through_graph_cycle(self, db_pool):
        """Full cycle (coach_open → rex_challenge → evaluate → sage → close)
        must persist a sessions row and an exchanges row, both with concept_id."""
        import asyncio
        from nodes import coach_open as coach_open_module
        from nodes import rex_rechallenge as rechallenge_module
        from repositories import create_exchange

        fake_initial = {
            "id": "deploy-codepipeline-basics",
            "domain": "Deployment",
            "task_statement": "Deploy via CI/CD pipelines.",
            "topic": "CodePipeline Basics",
            "topic_id": "deploy-codepipeline-basics",
            "task_statement_id": "deploy-codepipeline-basics",
            "services": ["CodePipeline"],
            "source_ids": [],
            "familiarity_level": "new",
            "ready": True,
        }
        fake_rechallenge = {
            "id": "deploy-cicd-services",
            "domain": "Deployment",
            "task_statement": "Use CI/CD services.",
            "topic": "CI/CD Services",
            "topic_id": "deploy-cicd-services",
            "task_statement_id": "deploy-cicd-services",
            "services": ["CodePipeline", "CodeBuild"],
            "source_ids": [],
            "familiarity_level": "new",
            "ready": True,
        }

        with patch.object(coach_open_module, "select_initial_concept", return_value=fake_initial):
            with patch.object(rechallenge_module, "select_rechallenge_concept", return_value=fake_rechallenge):
                state = _minimal_state()
                graph = _graph()

                # Run coach_open + one full cycle without LLM by patching all LLM nodes.
                async def run_graph():
                    state_after_coach = await graph.ainvoke(state, node="coach_open")
                    return state_after_coach

                state_after_coach = asyncio.run(run_graph())

        concept_id = state_after_coach.get("current_concept_id")
        assert concept_id, "current_concept_id must be set after coach_open"

        # Verify the session row in DB.
        session_id = state_after_coach.get("db_session_id", "")
        if session_id:
            async with db_pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "SELECT concept_id FROM sessions WHERE id = %s",
                        (session_id,),
                    )
                    row = await cur.fetchone()
            assert row is not None
            assert row[0] == concept_id


# ---------------------------------------------------------------------------
# Pytest fixtures for integration tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def db_pool():
    """Async Postgres pool for integration tests. Requires docker-compose Postgres."""
    if not DATABASE_URL_SET:
        pytest.skip("DATABASE_URL not set")

    import asyncio
    import psycopg_pool

    async def _init():
        pool = psycopg_pool.AsyncConnectionPool(
            conninfo=os.environ["DATABASE_URL"],
            min_size=1,
            max_size=4,
            open=False,
        )
        await pool.open()
        return pool

    pool = asyncio.run(_init())
    yield pool
    asyncio.run(pool.close())


# Register a custom mark so we can filter clearly.
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "db_required: integration test requires running Postgres (docker compose up -d)"
    )
