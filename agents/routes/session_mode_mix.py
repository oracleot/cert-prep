"""Phase 11 — App-controlled response_mode selection (60/40 single/multi mix).

The mix is approximated per prompt using a deterministic cycle-based pattern
that yields a 60/40 single-to-multiple ratio over the course of a session
without randomness (deterministic tests stay deterministic). The V1 mix:

    cycle 1 → single_response
    cycle 2 → multiple_response
    cycle 3 → single_response
    cycle 4 → multiple_response
    cycle 5 → single_response

For a default 2-cycle session this gives exactly one single + one multi
prompt (50/50); over a 5-cycle session it gives 3 single + 2 multi
(60/40). The pattern is intentionally cycle-aligned so a rechallenge can
flip the mode without surprising the user mid-prompt.

Kept out of ``routes/session.py`` so the route file stays under the
200-line hard rule and the mix is unit-testable in isolation.
"""
from __future__ import annotations

from option_types import ResponseMode

_SINGLE_CYCLES: frozenset[int] = frozenset({1, 3, 5})
_MULTI_CYCLES: frozenset[int] = frozenset({2, 4})


def pick_response_mode(cycle: int) -> ResponseMode:
    """Return the response_mode for the prompt at ``cycle`` (1-indexed)."""
    if cycle in _MULTI_CYCLES:
        return "multiple_response"
    if cycle in _SINGLE_CYCLES:
        return "single_response"
    # Fall back to single for cycles > 5 (clamped upstream).
    return "single_response"


__all__ = ["pick_response_mode"]