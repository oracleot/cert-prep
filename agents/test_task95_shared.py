"""Shared fixtures for Task 9.5 — Sage grounding tests."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


# ---------------------------------------------------------------------------
# Fake concept
# ---------------------------------------------------------------------------

FAKE_CONCEPT = {
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
    "facts": [
        "CodePipeline has at least three stages: Source, Build, Deploy.",
        "CodeBuild projects run in isolated build environments.",
    ],
    "traps": [
        "CodeBuild does NOT run inside a VPC by default; you must explicitly enable VPC mode.",
    ],
    "expected_answer_criteria": "Answer must mention at least one CodePipeline stage type.",
    "official_docs": ["https://docs.aws.amazon.com/codepipeline/latest/userguide/"],
    "skill_builder_links": ["https://skillbuilder.aws/labs/"],
    "lab_links": ["https://clouderlabs.example.com/codepipeline-lab"],
}


# ---------------------------------------------------------------------------
# Fake Sage LLM (sync + async)
# ---------------------------------------------------------------------------

class FakeSageResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class FakeSageLLM:
    """Async-capable LLM mock for sage_respond."""

    def __init__(self, content: str) -> None:
        self._content = content

    def invoke(self, *a, **k):
        return FakeSageResponse(self._content)

    async def ainvoke(self, *a, **k):
        return FakeSageResponse(self._content)


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def seed_state_with_challenge(concept: dict) -> dict:
    """Minimal state ready for sage_respond."""
    from test_task93_shared import _seed_state

    state = _seed_state()
    state.update({
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
            "scenario": "An engineer configures a pipeline.",
            "question": "Which stage is required?",
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
    return state


def run_sage_depth_sync(sage_module, state, fake_response: str) -> dict:
    """Run sage_depth async function from a sync test context.

    Fixed: submits the coroutine directly instead of double-wrapping
    pool.submit(asyncio.run, future.result()).
    """
    import concurrent.futures

    async def _run():
        return await sage_module.sage_depth(state, {})

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, _run())
        return future.result()
