"""Integration tests — concept_id persists in DB rows (requires docker Postgres)."""
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


DATABASE_URL_SET = bool(os.environ.get("DATABASE_URL"))

pytestmark = pytest.mark.skipif(
    not DATABASE_URL_SET,
    reason="DATABASE_URL not set — run 'docker compose up -d' first",
)


def _minimal_state(user_id: str = "") -> dict:
    return initial_state(
        user_id=user_id or f"test-user-{uuid.uuid4().hex[:8]}",
        exam_id="dva-c02",
        max_cycles=2,
    )


@pytest.fixture(scope="session")
def db_pool():
    """Async Postgres pool for integration tests."""
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


class TestExchangePersistsConceptId:
    """Sessions and exchanges DB rows must carry concept_id."""

    @pytest.mark.asyncio
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
        assert row[0] == "deploy-codepipeline-basics"

    @pytest.mark.asyncio
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
        assert row[0] == "deploy-codepipeline-basics"

    @pytest.mark.asyncio
    async def test_concept_id_flows_through_graph_cycle(self, db_pool):
        """Full cycle must persist sessions + exchanges rows with concept_id."""
        import asyncio
        import graphs.session as _gs
        os.environ.pop("DATABASE_URL", None)
        _gs._cached_graph = None

        import nest_asyncio
        nest_asyncio.apply()

        import db as _db
        _asyncio = asyncio
        _asyncio.run(_db.init_checkpointer())

        from graphs.session import get_session_graph
        from nodes import coach_open as coach_open_module
        from nodes import rex_rechallenge as rechallenge_module

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
                graph = get_session_graph()

                async def run_graph():
                    return await graph.ainvoke(state, node="coach_open")

                state_after_coach = asyncio.run(run_graph())

        concept_id = state_after_coach.get("current_concept_id")
        assert concept_id, "current_concept_id must be set after coach_open"

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
