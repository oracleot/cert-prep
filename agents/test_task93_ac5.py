"""Task 9.3 AC5 — no ready concept → session start fails clearly (422)."""
from __future__ import annotations

import sys
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from test_task93_shared import _node_graph, _seed_state

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from concepts.selector import NoReadyConcept

# ---------------------------------------------------------------------------
# AC5 — no ready concept → session start fails clearly (422)
# ---------------------------------------------------------------------------

class TestAC5_NoReadyConceptFailsSession:
    """Session start must return HTTP 422 when no ready concept exists."""

    def test_session_start_raises_422_when_no_ready_concept_for_domain(self):
        """POST /session/start must return HTTP 422 with a domain-named message."""
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
            "coach_open must raise HTTPException(status_code=422) from NoReadyConcept."
        )
        body = response.json()
        assert "Deployment" in str(body) or "NoReadyConcept" in str(body)

    def test_session_start_raises_422_for_unknown_exam(self):
        """Unknown exam with no concept directory must return HTTP 422."""
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
            side_effect=NoReadyConcept(exam_id="unknown-exam-xyz"),
        ):
            response = client.post(
                "/session/start",
                json={
                    "user_id": f"test-user-{uuid.uuid4().hex[:8]}",
                    "exam_id": "unknown-exam-xyz",
                    "max_cycles": 2,
                },
            )

        assert response.status_code == 422, (
            f"Expected 422 for unknown exam; got {response.status_code}"
        )

    def test_rechallenge_node_raises_http_exception_on_no_ready_concept(self):
        """rex_rechallenge must raise HTTPException(422) instead of silent fallback."""
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

        state = _seed_state()
        state["current_concept_id"] = fake_concept["id"]
        state["current_domain"] = "Deployment"
        state["current_challenge"] = {
            "domain": "Deployment",
            "topic": "CodePipeline Basics",
            "topic_id": fake_concept["id"],
            "task_statement_id": fake_concept["id"],
            "task_statement": fake_concept["task_statement"],
            "services": fake_concept["services"],
            "source_ids": [],
            "familiarity_level": "new",
            "scenario": "Test.",
            "question": "What?",
            "difficulty": "medium",
            "concept_id": fake_concept["id"],
        }
        graph = _node_graph()

        with patch.object(
            rechallenge_module,
            "select_rechallenge_concept",
            side_effect=NoReadyConcept(domain="Deployment"),
        ):
            with pytest.raises(FastAPIHTTPException) as exc_info:
                graph.invoke(state, node="rex_rechallenge")

        assert exc_info.value.status_code == 422, (
            f"Expected HTTPException(422); got {exc_info.value.status_code}"
        )
