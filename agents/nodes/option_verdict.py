"""Phase 11 — deterministic option-based verdict computation.

Extracted from ``nodes/evaluate_answer.py`` so the main node file stays
under the 200-line hard rule. All functions are pure: they take a challenge
dict + the learner's selected labels and return the verdict payload that
flows into ``last_evaluation``.
"""
from __future__ import annotations

import re
from typing import Any

from option_types import (
    OPTION_LABELS,
    ResponseMode,
    is_option_label,
    normalize_option_labels,
)


def extract_selected_labels(state: dict[str, Any]) -> list[str]:
    """Return the learner's selected labels in A/B/C/D order.

    Accepts either ``state["selected_labels"]`` (set by the route from the
    submit body) or ``state["user_answer"]`` formatted as a comma-separated
    label list (``"A,C"`` / ``"A, C"``) — the latter is a forgiving
    fallback so direct tests / older callers keep working.
    """
    direct = state.get("selected_labels")
    if isinstance(direct, list):
        return normalize_option_labels(direct)
    raw = state.get("user_answer") or ""
    if not raw:
        return []
    tokens = [tok.strip().upper() for tok in re.split(r"[,\s]+", raw) if tok.strip()]
    return normalize_option_labels(t for t in tokens if is_option_label(t))


def challenge_is_option_based(challenge: dict[str, Any]) -> bool:
    """A challenge is option-based when it ships a non-empty options list."""
    options = challenge.get("options")
    return isinstance(options, list) and len(options) == len(OPTION_LABELS)


def build_reasoning(
    mode: ResponseMode,
    outcome: str,
    selected: list[str],
    correct: list[str],
    missed: list[str],
    incorrect: list[str],
) -> str:
    if outcome == "correct":
        if mode == "single_response":
            return f"Selected {selected[0]!r} — matches the single correct answer."
        return f"Selected {', '.join(selected)!r} — exact match for the answer key."
    bits: list[str] = []
    if missed:
        bits.append(f"missed {', '.join(missed)!r}")
    if incorrect:
        bits.append(f"incorrectly chose {', '.join(incorrect)!r}")
    if not bits:
        bits.append("no options selected")
    return "Incorrect — " + "; ".join(bits) + "."


def compute_option_verdict(
    challenge: dict[str, Any],
    selected: list[str],
) -> dict[str, Any]:
    """Compute the binary verdict + label breakdown for an option-based prompt.

    Multi-response scoring is exact-match: the learner must select the entire
    answer_key set. Choosing only a subset (including a single label on a
    multi-response prompt) is incorrect, with the missing labels surfaced in
    ``missed_labels`` and any extra selections surfaced in ``incorrect_labels``.
    """
    correct = normalize_option_labels(challenge.get("answer_key") or [])
    selected_set = set(selected)
    correct_set = set(correct)
    missed = sorted(correct_set - selected_set)
    incorrect = sorted(selected_set - correct_set)
    outcome = "correct" if selected_set == correct_set and len(selected_set) > 0 else "incorrect"
    mode = challenge.get("response_mode") or "single_response"
    reasoning = build_reasoning(mode, outcome, selected, correct, missed, incorrect)
    return {
        "outcome": outcome,
        "reasoning": reasoning,
        "selected_labels": selected,
        "correct_labels": correct,
        "missed_labels": missed,
        "incorrect_labels": incorrect,
    }