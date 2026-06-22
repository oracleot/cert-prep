"""Task 9.3 test contract — closed-book concept selection in session router.

Failing tests that define done:
  AC1  →  session selects conceptId before Rex runs
  AC2  →  Rex receives concept packet, no free-roam
  AC3  →  challenge output stores conceptId, domain, topic, task statement, source IDs
  AC4  →  rechallenge uses app-selected weak/uncovered/related concept
  AC5  →  no ready concept → session start fails clearly (422)

Expected failures on current code:
  - initial_state() is missing concept fields → AC1/AC3 tests fail
  - select_rechallenge_concept(None) not guarded → AC4 edge-case fails
  - rex_rechallenge.py source check fails if import not present
  - integration tests fail if graph nodes don't wire concept fields

Run:  cd agents && python -m pytest test_task93_concept_closed_book.py -v
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from concepts.selector import NoReadyConcept, select_rechallenge_concept
from graphs.session import get_session_graph
from state import initial_state


# ---------------------------------------------------------------------------
# Mock LLM for tests that need to run rex_challenge / rex_rechallenge without API keys
# ---------------------------------------------------------------------------

class FakeLLMResponse:
    def __init__(self, content: str = '') -> None:
        self.content = content


class FakeLLM:
    """Minimal mock matching the ChatOpenAI interface used by the session graph nodes."""

    def __init__(self, response_content: str = '') -> None:
        self._content = response_content

    def invoke(self, *a, **k):
        return FakeLLMResponse(self._content)

    async def ainvoke(self, *a, **k):
        return FakeLLMResponse(self._content)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_state(**kwargs) -> dict:
    base = initial_state(
        user_id=kwargs.get("user_id", f"test-{uuid.uuid4().hex[:8]}"),
        exam_id="dva-c02",
        max_cycles=2,
    )
    base.update(kwargs)
    return base


def _node_graph():
    """Graph via get_session_graph() which wraps in NodeAwareGraph supporting node= kwarg.

    Uses InMemorySaver when DATABASE_URL is absent (no Postgres required for unit tests).
    Ensures db.init_checkpointer() runs first so _checkpointer is initialized.
    """
    import os
    import graphs.session as _gs

    # Ensure DATABASE_URL is unset so checkpointer falls back to InMemorySaver.
    os.environ.pop("DATABASE_URL", None)

    # Reset the cached graph so each test gets a fresh wrapper.
    _gs._cached_graph = None

    # Pre-initialize the checkpointer so get_session_graph() can use it.
    import db as _db
    # init_checkpointer is async; run in a fresh event loop.
    import asyncio as _asyncio
    _asyncio.run(_db.init_checkpointer())

    return get_session_graph()


# ---------------------------------------------------------------------------
# AC1 — session selects conceptId before Rex runs
# ---------------------------------------------------------------------------

class TestAC1_SessionSelectsConceptId:
    """App/session code selects conceptId before Rex runs."""

    def test_initial_state_declares_concept_fields(self):
        """All concept fields must be declared in initial_state().

        Fails until state.py adds current_concept_id, current_topic,
        current_task_statement, current_services, current_source_ids,
        familiarity_level to initial_state().
        """
        state = _seed_state()
        required_fields = [
            "current_concept_id",
            "current_topic",
            "current_task_statement",
            "current_services",
            "current_source_ids",
            "familiarity_level",
            "rex_difficulty",
        ]
        missing = [f for f in required_fields if f not in state]
        assert not missing, (
            f"initial_state() is missing concept fields: {missing}. "
            "Add them to AppState TypedDict and initial_state() in state.py."
        )

    def test_coach_open_stamps_concept_id_into_state(self):
        """coach_open must return current_concept_id in state dict.

        Fails until coach_open.py returns current_concept_id from the selected
        concept, and initial_state() includes the field.
        """
        fake_concept = {
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
        }

        from nodes import coach_open as coach_open_module

        with patch.object(coach_open_module, "select_initial_concept", return_value=fake_concept):
            state = _seed_state()
            graph = _node_graph()
            result = graph.invoke(state, node="coach_open")

        assert "current_concept_id" in result, (
            "coach_open must return current_concept_id in state. "
            "Check that coach_open calls select_initial_concept and returns "
            "the concept['id'] as current_concept_id."
        )
        assert result["current_concept_id"] == "deploy-codepipeline-basics", (
            f"current_concept_id should be 'deploy-codepipeline-basics', "
            f"got {result['current_concept_id']!r}"
        )

    def test_coach_open_stamps_task_statement_and_services(self):
        """coach_open must propagate task_statement, services, source_ids to state."""
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
            state = _seed_state()
            graph = _node_graph()
            result = graph.invoke(state, node="coach_open")

        assert result.get("current_task_statement") == "Deploy application updates using CI/CD pipelines."
        assert result.get("current_services") == ["CodePipeline", "CodeBuild"]
        assert result.get("current_source_ids") == ["sb-deploy-pipelines"]
        assert result.get("familiarity_level") == "new"


# ---------------------------------------------------------------------------
# AC2 — Rex receives concept packet, no free-roam
# AC3 — challenge output stores conceptId, domain, topic, task statement, source IDs
# ---------------------------------------------------------------------------

class TestAC2_AC3_ChallengeOutputConceptFields:
    """Challenge dict must include conceptId, domain, topic, task_statement, source IDs."""

    def test_rex_challenge_output_carries_concept_id(self):
        """rex_challenge must return current_challenge.concept_id from state.

        Fails until rex_challenge.py includes concept_id in the returned dict.
        """
        fake_concept = {
            "id": "deploy-codepipeline-basics",
            "domain": "Deployment",
            "task_statement": "Deploy via CI/CD.",
            "topic": "CodePipeline Basics",
            "topic_id": "deploy-codepipeline-basics",
            "task_statement_id": "deploy-codepipeline-basics",
            "services": ["CodePipeline"],
            "source_ids": ["sb-deploy-pipelines"],
            "familiarity_level": "new",
            "ready": True,
        }

        from nodes import coach_open as coach_open_module

        with patch.object(coach_open_module, "select_initial_concept", return_value=fake_concept):
            state = _seed_state()
            graph = _node_graph()
            state_after_coach = graph.invoke(state, node="coach_open")

            # Patch at the module where rex_challenge imported it.
            with patch("nodes.rex_challenge.get_llm", return_value=FakeLLM('{"domain":"Deployment","topic":"CodePipeline Basics","scenario":"Test scenario.","question":"What?"}')):
                result = graph.invoke(state_after_coach, node="rex_challenge")

        challenge = result.get("current_challenge", {})
        assert "concept_id" in challenge, (
            "current_challenge must include concept_id. "
            "rex_challenge.py must copy state['current_concept_id'] into the challenge dict."
        )
        assert challenge.get("concept_id") == "deploy-codepipeline-basics"

    def test_rex_challenge_output_includes_domain_topic_task_statement(self):
        """Challenge must carry domain, topic, task_statement, services, source_ids."""
        fake_concept = {
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
        }

        from nodes import coach_open as coach_open_module

        with patch.object(coach_open_module, "select_initial_concept", return_value=fake_concept):
            state = _seed_state()
            graph = _node_graph()
            state_after_coach = graph.invoke(state, node="coach_open")

            with patch("nodes.rex_challenge.get_llm", return_value=FakeLLM('{"domain":"Deployment","topic":"CodePipeline Basics","scenario":"Test scenario.","question":"What?"}')):
                result = graph.invoke(state_after_coach, node="rex_challenge")

        challenge = result.get("current_challenge", {})
        assert challenge.get("domain") == "Deployment"
        assert challenge.get("task_statement") == "Deploy via CI/CD pipelines."
        assert challenge.get("services") == ["CodePipeline", "CodeBuild"]
        assert challenge.get("source_ids") == ["sb-deploy-pipelines"]


# ---------------------------------------------------------------------------
# AC4 — rechallenge uses app-selected weak/uncovered/related concept, no free-roam
# ---------------------------------------------------------------------------

class TestAC4_RechallengeUsesAppSelectedConcept:
    """Rechallenge must call select_rechallenge_concept, not free-roam."""

    def test_rex_rechallenge_node_calls_select_rechallenge_concept(self):
        """rex_rechallenge.py must import and call select_rechallenge_concept.

        Fails until the import is added to rex_rechallenge.py.
        """
        source = (_AGENTS_DIR / "nodes" / "rex_rechallenge.py").read_text()
        assert "select_rechallenge_concept" in source, (
            "rex_rechallenge.py must import select_rechallenge_concept from "
            "concepts.selector — not free-roam with topic_stats or hardcoded logic."
        )

    def test_rechallenge_returns_different_concept_id(self):
        """After rechallenge, current_concept_id must differ from initial."""
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
                state = _seed_state()
                graph = _node_graph()
                state_after_coach = graph.invoke(state, node="coach_open")

                # Provide a minimal current_challenge so rechallenge node doesn't crash.
                state_after_coach["current_challenge"] = {
                    "domain": "Deployment",
                    "topic": "CodePipeline Basics",
                    "topic_id": "deploy-codepipeline-basics",
                    "task_statement_id": "deploy-codepipeline-basics",
                    "task_statement": "Deploy via CI/CD.",
                    "services": ["CodePipeline"],
                    "source_ids": [],
                    "familiarity_level": "new",
                    "scenario": "Test.",
                    "question": "What?",
                    "difficulty": "medium",
                    "concept_id": initial_concept["id"],
                }
                # Patch exchange_history so rechallenge selector doesn't need DB.
                def fake_history(*a, **k):
                    return [{"concept_id": initial_concept["id"], "outcome": "correct"}]

                with patch("concepts.selector.exchange_history_for_user", fake_history):
                    with patch("nodes.rex_rechallenge.get_llm", return_value=FakeLLM('{"domain":"Deployment","topic":"CI/CD Services","scenario":"Test scenario.","question":"What?"}')):
                        result = graph.invoke(state_after_coach, node="rex_rechallenge")

        new_cid = result.get("current_concept_id")
        assert new_cid != "deploy-codepipeline-basics", (
            f"Rechallenge must change current_concept_id; got {new_cid!r}"
        )
        assert result.get("current_domain") == "Deployment"

    def test_rechallenge_output_carries_new_concept_packet(self):
        """After rechallenge, the new concept's task_statement/services/source_ids
        must be reflected in the challenge output."""
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
            "task_statement": "Use CI/CD services: CodePipeline, CodeBuild, CodeDeploy.",
            "topic": "CI/CD Services",
            "topic_id": "deploy-cicd-services",
            "task_statement_id": "deploy-cicd-services",
            "services": ["CodePipeline", "CodeBuild", "CodeDeploy"],
            "source_ids": ["sb-cicd-services"],
            "familiarity_level": "new",
            "ready": True,
        }

        from nodes import coach_open as coach_open_module
        from nodes import rex_rechallenge as rechallenge_module

        with patch.object(coach_open_module, "select_initial_concept", return_value=initial_concept):
            with patch.object(rechallenge_module, "select_rechallenge_concept", return_value=rechallenge_concept):
                state = _seed_state()
                graph = _node_graph()
                state_after_coach = graph.invoke(state, node="coach_open")
                state_after_coach["current_challenge"] = {
                    "domain": "Deployment",
                    "topic": "CodePipeline Basics",
                    "topic_id": "deploy-codepipeline-basics",
                    "task_statement_id": "deploy-codepipeline-basics",
                    "task_statement": "Deploy via CI/CD.",
                    "services": ["CodePipeline"],
                    "source_ids": [],
                    "familiarity_level": "new",
                    "scenario": "Test.",
                    "question": "What?",
                    "difficulty": "medium",
                    "concept_id": initial_concept["id"],
                }

                def fake_history(*a, **k):
                    return [{"concept_id": initial_concept["id"], "outcome": "correct"}]

                with patch("concepts.selector.exchange_history_for_user", fake_history):
                    with patch("nodes.rex_rechallenge.get_llm", return_value=FakeLLM('{"domain":"Deployment","topic":"CI/CD Services","scenario":"Test scenario.","question":"What?"}')):
                        result = graph.invoke(state_after_coach, node="rex_rechallenge")

        challenge = result.get("current_challenge", {})
        assert challenge.get("concept_id") == "deploy-cicd-services"
        assert challenge.get("task_statement") == "Use CI/CD services: CodePipeline, CodeBuild, CodeDeploy."
        assert challenge.get("services") == ["CodePipeline", "CodeBuild", "CodeDeploy"]
        assert challenge.get("source_ids") == ["sb-cicd-services"]


# ---------------------------------------------------------------------------
# AC4 edge case — select_rechallenge_concept with empty/None domain
# ---------------------------------------------------------------------------

class TestAC4_SelectRechallengeEdgeCases:
    """Edge cases for select_rechallenge_concept."""

    def test_empty_domain_string_raises_no_ready_concept(self):
        """Passing empty string domain must raise NoReadyConcept, not crash."""
        with pytest.raises(NoReadyConcept):
            select_rechallenge_concept(
                exam_id="dva-c02",
                domain="",
                previous_concept_id="any-id",
                user_id="test-user",
            )

    def test_nonexistent_domain_raises_no_ready_concept(self):
        """Unknown domain must raise NoReadyConcept with the domain name."""
        with pytest.raises(NoReadyConcept) as exc_info:
            select_rechallenge_concept(
                exam_id="dva-c02",
                domain="ZetaClassDomain",
                previous_concept_id="any-id",
                user_id="test-user",
            )
        assert "ZetaClassDomain" in str(exc_info.value)


# ---------------------------------------------------------------------------
# AC5 — no ready concept → session start fails clearly (422)
# ---------------------------------------------------------------------------

class TestAC5_NoReadyConceptFailsSession:
    """Session start must return HTTP 422 when no ready concept exists."""

    def test_session_start_raises_422_when_no_ready_concept_for_domain(self):
        """POST /session/start must return HTTP 422 with a domain-named message.

        Fails until coach_open.py propagates NoReadyConcept as HTTPException(422)
        and routes/session.py wraps it correctly.
        """
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
        """rex_rechallenge must raise HTTPException(422) instead of silent fallback.

        The node converts NoReadyConcept → HTTPException(status_code=422).
        The route then propagates this as a 422 response to the client.
        """
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
