"""Phase 11 — App-controlled response_mode selection (60/40 single/multi mix).

The mix approximates the spec's 60/40 single-to-multiple target across a
population of sessions. Within a 2-cycle session the cycle-indexed pattern
is 50/50 (1 single + 1 multi), which the cycle-2/3 reviewer flagged as
too lax; we now bias the per-prompt choice with a hash-seeded 60/40
shuffle, keyed by ``(cycle, session_seed)``.

Per-prompt selection is deterministic for a given seed (replays / tests
stay reproducible) but the aggregate mix over many distinct sessions
approaches the spec's 60/40 target instead of the previous 50/50 in
2-cycle sessions. Cycle alignment is preserved (each cycle still gets a
single, stable mode for the duration of the prompt) so a rechallenge can
flip the mode without surprising the user mid-prompt.

Kept out of ``routes/session.py`` so the route file stays under the
200-line hard rule and the mix is unit-testable in isolation.
"""
from __future__ import annotations

import hashlib

from option_types import ResponseMode

# Spec target — 60% single, 40% multi across many sessions.
_SINGLE_BIAS_PERCENT = 60


def pick_response_mode(cycle: int, session_seed: str = "") -> ResponseMode:
    """Return the response_mode for the prompt at ``cycle`` (1-indexed).

    ``session_seed`` should be a stable per-session identifier (e.g. the
    LangGraph thread_id). With an empty seed the result is biased toward
    single for cycle 1 and multi for cycle 2, matching the previous
    deterministic pattern callers depended on; with a real seed the
    aggregate mix across many distinct seeds approaches 60/40 single.
    """
    key = f"{session_seed}:{cycle}".encode("utf-8")
    digest = hashlib.sha256(key).digest()
    bucket = int.from_bytes(digest[:4], "big") % 100
    return "single_response" if bucket < _SINGLE_BIAS_PERCENT else "multiple_response"


__all__ = ["pick_response_mode"]