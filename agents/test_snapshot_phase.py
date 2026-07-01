"""Phase 11 — ``_snapshot_phase`` contract tests.

Pins the next-node → SessionPhase mapping so a future refactor cannot
collapse the post-evaluation pre-Sage-done state back to ``"ready"``
(which would drop the "cannot proceed until Sage completes" lock
that survives snapshot/restore).
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


class _Snap:
    """Minimal stand-in for langgraph ``StateSnapshot`` (only needs .next)."""

    def __init__(self, next_nodes):
        self.next = list(next_nodes) if next_nodes else []


class TestSnapshotPhase:
    """Every non-end next-node set maps to the locked client phase."""

    def test_empty_next_is_summary(self):
        from routes.session import _snapshot_phase
        assert _snapshot_phase(_Snap(None)) == "summary"
        assert _snapshot_phase(_Snap([])) == "summary"

    def test_sage_node_in_next_is_streaming_sage(self):
        from routes.session import _snapshot_phase
        # Sage is currently running — the snapshot MUST surface
        # streaming_sage so the client locks the input after reload.
        assert _snapshot_phase(_Snap(["sage_depth"])) == "streaming_sage"
        assert _snapshot_phase(_Snap(["sage_explain"])) == "streaming_sage"

    def test_rechallenge_or_coach_close_is_sage_done(self):
        from routes.session import _snapshot_phase
        # Sage finished for the current cycle; the learner may advance.
        assert _snapshot_phase(_Snap(["rex_rechallenge"])) == "sage_done"
        assert _snapshot_phase(_Snap(["coach_close"])) == "sage_done"

    def test_rex_challenge_or_coach_open_is_loading_challenge(self):
        from routes.session import _snapshot_phase
        assert _snapshot_phase(_Snap(["rex_challenge"])) == "loading_challenge"
        assert _snapshot_phase(_Snap(["coach_open"])) == "loading_challenge"

    def test_evaluate_answer_paused_is_ready(self):
        from routes.session import _snapshot_phase
        # interrupt_before=["evaluate_answer", "rex_rechallenge"] means the
        # graph pauses here waiting for the learner to submit.
        assert _snapshot_phase(_Snap(["evaluate_answer"])) == "ready"
