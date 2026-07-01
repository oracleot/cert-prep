"""Phase 11 — 1-label multiple_response acceptance test.

Extracted from ``test_phase11_rex_integration.py`` so the rex
integration module stays under the 200-line hard rule. The spec
(docs/option-based-session-spec.md) allows 1-2 correct options for
multiple_response; this test pins the 1-label shape so a future
refactor cannot tighten the validator back to the 'exactly 2' shape
reviewers flagged in cycle 2.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from test_phase11_rex_integration import (  # noqa: E402  (shared fixtures)
    _FAKE_CONCEPT,
    _multi_response_payload,
)
from test_task93_shared import FakeLLM, _node_graph, _seed_state  # noqa: E402


def _one_label_multi_response_payload() -> str:
    return json.dumps({
        "domain": "Deployment",
        "topic": "CI/CD Services",
        "scenario": "An engineer selects AWS managed CI/CD services for a pipeline.",
        "question": "Which ONE service runs a managed build?",
        "response_mode": "multiple_response",
        "options": [
            {"label": "A", "text": "CodePipeline"},
            {"label": "B", "text": "CodeBuild"},
            {"label": "C", "text": "Lambda"},
            {"label": "D", "text": "S3"},
        ],
        "answer_key": ["B"],
    })


class TestMultiResponseOneLabel:
    def test_multi_response_with_one_label_is_accepted(self):
        from nodes import coach_open as coach_open_module
        concept = dict(_FAKE_CONCEPT)
        with patch.object(coach_open_module, "select_initial_concept", return_value=concept):
            state = _seed_state()
            graph = _node_graph()
            state_after_coach = graph.invoke(state, node="coach_open")
            state_after_coach["current_response_mode"] = "multiple_response"

            with patch(
                "nodes.rex_challenge.get_llm",
                return_value=FakeLLM(_one_label_multi_response_payload()),
            ):
                result = graph.invoke(state_after_coach, node="rex_challenge")

        ch = result["current_challenge"]
        assert ch["response_mode"] == "multiple_response"
        assert ch["answer_key"] == ["B"]
