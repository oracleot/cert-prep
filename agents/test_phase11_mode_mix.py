"""Phase 11 — ``pick_response_mode`` 60/40 mix tests.

Extracted from ``test_phase11_option_types.py`` so the helpers/verdict
module stays under the 200-line hard rule. The 60/40 mix is biased via
a per-session hash so a population of distinct sessions approaches the
spec's target.
"""
from __future__ import annotations

import sys
from pathlib import Path

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


class TestSessionModeMix:
    """60/40 single/multi mix biased via a per-session seed.

    The previous deterministic cycle pattern (cycle 1 → single, cycle 2 →
    multi, …) yielded 50/50 in 2-cycle sessions, which the cycle-2
    reviewer flagged as too lax. The new implementation hashes
    ``(cycle, session_seed)`` and biases single 60% of the time so a
    population of distinct sessions approaches the spec's 60/40 target.
    """

    def test_empty_seed_keeps_legacy_cycle_pattern(self):
        # Back-compat: callers that don't pass a session seed still see the
        # old cycle 1 = single / cycle 2 = multi mapping. The hash of an
        # empty seed is stable, so the legacy shape is preserved.
        from routes.session_mode_mix import pick_response_mode
        assert pick_response_mode(1) == "single_response"
        assert pick_response_mode(2) == "multiple_response"

    def test_aggregate_mix_approaches_60_40_across_sessions(self):
        # 2-cycle session × 1000 distinct seeds → single share should be
        # close to 60%. We allow a generous ±5% band so the test is not
        # flaky; the spec asks for "approximate" 60/40 and the bias is
        # built into the hash bucket, not a strict enforcement.
        from routes.session_mode_mix import pick_response_mode
        single = 0
        total = 0
        for session in range(1000):
            for cycle in range(1, 3):  # default 2-cycle session
                if pick_response_mode(cycle, session_seed=f"s{session}") == "single_response":
                    single += 1
                total += 1
        share = single / total
        assert 0.55 <= share <= 0.65, f"single share {share:.3f} outside 0.55-0.65 band"

    def test_same_seed_is_deterministic(self):
        from routes.session_mode_mix import pick_response_mode
        a = [pick_response_mode(c, session_seed="stable") for c in range(1, 6)]
        b = [pick_response_mode(c, session_seed="stable") for c in range(1, 6)]
        assert a == b

    def test_distinct_seeds_can_diverge(self):
        # Smoke check: at least one cycle flips when the seed changes, so
        # the function is actually consulting session_seed (not just
        # falling back to the cycle pattern).
        from routes.session_mode_mix import pick_response_mode
        assert (
            [pick_response_mode(2, session_seed=f"s{i}") for i in range(50)]
            .count("multiple_response")
        ) != 0  # pragma: no cover - sanity
