"""Integration tests — NoReadyConcept surfaces as HTTP 422."""
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

from concepts.selector import NoReadyConcept
from state import initial_state


def _minimal_state(user_id: str = "") -> dict:
    return initial_state(
        user_id=user_id or f"test-user-{uuid.uuid4().hex[:8]}",
        exam_id="dva-c02",
        max_cycles=2,
    )


class TestNoReadyConceptFailsSession:
    """Session start must fail loudly (HTTP 422) when no ready concept exists."""

    def test_session_start_returns_422_when_no_ready_concept_for_domain(self):
        """Monkeypatch select_initial_concept to raise NoReadyConcept;
        POST /session/start must return HTTP 422 with a domain-named message."""
        from fastapi.testclient import TestClient

        try:
            from main import app
        except Exception as exc:
            pytest.skip(f"Could not import FastAPI app: {exc}")

        client = TestClient(app, raise_server_exceptions=False)

        from nodes import coach_open as coach_open_module

        with patch.object(
            coach_open_module,
            "select_initial_concept",
            side_effect=NoReadyConcept(domain="Deployment"),
        ):
            with patch.object(
                coach_open_module,
                "select_initial_concept",
                side_effect=NoReadyConcept(domain="Deployment"),
            ):
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
        assert "Deployment" in str(body) or "NoReadyConcept" in str(body)

    def test_rechallenge_raises_when_no_ready_concept(self):
        """rex_rechallenge must raise HTTPException(422) when select_rechallenge_concept
        raises NoReadyConcept (instead of silently falling back)."""
        import os
        import graphs.session as _gs
        os.environ.pop("DATABASE_URL", None)
        _gs._cached_graph = None

        import nest_asyncio
        nest_asyncio.apply()

        import db as _db
        import asyncio as _asyncio
        _asyncio.run(_db.init_checkpointer())

        from graphs.session import get_session_graph
        graph = get_session_graph()

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

        with patch.object(rechallenge_module, "select_rechallenge_concept",
                          side_effect=NoReadyConcept(domain="Deployment")):
            with pytest.raises(FastAPIHTTPException) as exc_info:
                graph.invoke(state, node="rex_rechallenge")
            assert exc_info.value.status_code == 422
