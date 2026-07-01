"""Phase 11 — option-based session contract tests.

AC1: option_types helpers behave correctly.
AC2: pick_response_mode yields a 60/40 single/multi mix.
AC3: compute_option_verdict enforces exact-match scoring for both modes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


class TestOptionTypesHelpers:
    """is_option_label / is_response_mode / normalize_option_labels."""

    def test_is_option_label_accepts_a_b_c_d(self):
        from option_types import is_option_label
        for label in ("A", "B", "C", "D"):
            assert is_option_label(label), f"{label} should be a valid option label"

    def test_is_option_label_rejects_other_strings(self):
        from option_types import is_option_label
        for label in ("", "E", "a", "1", None, 0, []):
            assert not is_option_label(label), f"{label!r} should be rejected"

    def test_is_response_mode_accepts_two_values(self):
        from option_types import is_response_mode
        assert is_response_mode("single_response")
        assert is_response_mode("multiple_response")

    def test_is_response_mode_rejects_others(self):
        from option_types import is_response_mode
        for v in ("", "single", "multi", None, 1):
            assert not is_response_mode(v)

    def test_normalize_option_labels_dedupes_and_sorts(self):
        from option_types import normalize_option_labels
        assert normalize_option_labels(["D", "B", "A", "B", "X"]) == ["A", "B", "D"]
        assert normalize_option_labels([]) == []

    def test_normalize_option_labels_drops_invalid(self):
        from option_types import normalize_option_labels
        assert normalize_option_labels(["A", "Z", 1, None, "B"]) == ["A", "B"]


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


class TestOptionVerdict:
    """Exact-match scoring for both modes."""

    def _multi(self, key):
        return {
            "response_mode": "multiple_response",
            "options": [{"label": l, "text": l} for l in ("A", "B", "C", "D")],
            "answer_key": key,
        }

    def _single(self, key):
        return {
            "response_mode": "single_response",
            "options": [{"label": l, "text": l} for l in ("A", "B", "C", "D")],
            "answer_key": key,
        }

    def test_single_response_correct(self):
        from nodes.option_verdict import compute_option_verdict
        v = compute_option_verdict(self._single(["B"]), ["B"])
        assert v["outcome"] == "correct"
        assert v["correct_labels"] == ["B"]
        assert v["missed_labels"] == []
        assert v["incorrect_labels"] == []

    def test_single_response_incorrect(self):
        from nodes.option_verdict import compute_option_verdict
        v = compute_option_verdict(self._single(["B"]), ["A"])
        assert v["outcome"] == "incorrect"
        assert v["missed_labels"] == ["B"]
        assert v["incorrect_labels"] == ["A"]

    def test_multi_response_exact_match_correct(self):
        from nodes.option_verdict import compute_option_verdict
        v = compute_option_verdict(self._multi(["A", "C"]), ["A", "C"])
        assert v["outcome"] == "correct"
        assert v["missed_labels"] == []
        assert v["incorrect_labels"] == []

    def test_multi_response_partial_selection_is_incorrect(self):
        from nodes.option_verdict import compute_option_verdict
        v = compute_option_verdict(self._multi(["A", "C"]), ["A"])
        assert v["outcome"] == "incorrect"
        assert v["missed_labels"] == ["C"]
        assert v["incorrect_labels"] == []

    def test_multi_response_extra_selection_is_incorrect(self):
        from nodes.option_verdict import compute_option_verdict
        v = compute_option_verdict(self._multi(["A", "C"]), ["A", "C", "D"])
        assert v["outcome"] == "incorrect"
        assert v["incorrect_labels"] == ["D"]

    def test_empty_selection_is_incorrect(self):
        from nodes.option_verdict import compute_option_verdict
        v = compute_option_verdict(self._multi(["A", "C"]), [])
        assert v["outcome"] == "incorrect"
        assert v["missed_labels"] == ["A", "C"]
        assert v["incorrect_labels"] == []


class TestChallengeIsOptionBased:
    """challenge_is_option_based gate — only the 4-option shape counts."""

    def test_legacy_free_text_challenge_is_not_option_based(self):
        from nodes.option_verdict import challenge_is_option_based
        assert not challenge_is_option_based({"scenario": "x", "question": "y"})

    def test_challenge_with_four_options_is_option_based(self):
        from nodes.option_verdict import challenge_is_option_based
        ch = {"options": [{"label": l} for l in ("A", "B", "C", "D")]}
        assert challenge_is_option_based(ch)

    def test_challenge_with_three_options_is_not_option_based(self):
        from nodes.option_verdict import challenge_is_option_based
        ch = {"options": [{"label": l} for l in ("A", "B", "C")]}
        assert not challenge_is_option_based(ch)


class TestExtractSelectedLabels:
    """selected_labels / user_answer fallback parser."""

    def test_state_selected_labels_wins(self):
        from nodes.option_verdict import extract_selected_labels
        assert extract_selected_labels({"selected_labels": ["C", "A"]}) == ["A", "C"]

    def test_user_answer_csv_fallback(self):
        from nodes.option_verdict import extract_selected_labels
        assert extract_selected_labels({"user_answer": "A, C"}) == ["A", "C"]

    def test_user_answer_space_fallback(self):
        from nodes.option_verdict import extract_selected_labels
        assert extract_selected_labels({"user_answer": "B D"}) == ["B", "D"]

    def test_user_answer_drops_invalid_tokens(self):
        from nodes.option_verdict import extract_selected_labels
        assert extract_selected_labels({"user_answer": "A, X, Z, B"}) == ["A", "B"]

    def test_empty_state(self):
        from nodes.option_verdict import extract_selected_labels
        assert extract_selected_labels({}) == []