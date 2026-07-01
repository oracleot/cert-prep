"""Phase 11 — Rex option-based prompt snippets.

Kept separate from ``rex.py`` so the main challenge/rechallenge prompt
builders stay under the 200-line file limit. The functions here assemble the
"4 labeled options + answer key" block that follows the standard
scenario/question output shape.

The response_mode is app-controlled (callers pass it in); Rex only has to
emit the right number of correct labels for the supplied mode.
"""
from __future__ import annotations

from option_types import OPTION_LABELS, ResponseMode, max_labels_for_mode


# Append to the JSON shape in the user prompt — kept verbatim so the LLM
# is forced into the exact contract.
OPTIONS_JSON_BLOCK = """{
  "domain": "<domain>",
  "topic": "<topic>",
  "scenario": "<2-4 sentence operational scenario>",
  "question": "<precise question>",
  "response_mode": "<single_response|multiple_response>",
  "options": [
    {"label": "A", "text": "<distinct plausible option>"},
    {"label": "B", "text": "<distinct plausible option>"},
    {"label": "C", "text": "<distinct plausible option>"},
    {"label": "D", "text": "<distinct plausible option>"}
  ],
  "answer_key": ["<correct label(s) per response_mode>"]
}"""


def option_mode_directive(mode: ResponseMode) -> str:
    """Tell Rex the per-mode rules: number of correct labels, exact-match."""
    max_correct = max_labels_for_mode(mode)
    if mode == "single_response":
        return (
            f"response_mode = single_response. Exactly {max_correct} option is "
            "correct. answer_key must contain exactly one label from A/B/C/D."
        )
    return (
        f"response_mode = multiple_response. Up to {max_correct} options are "
        "correct in V1. answer_key must contain 1 or 2 labels from A/B/C/D; "
        "the learner must pick the exact set for the answer to count."
    )


def distractor_rules_directive() -> str:
    return (
        "Distractor rules:\n"
        "- Each of the three wrong options must be plausible and wrong for a "
        "distinct, specific reason (not just a paraphrase of the correct one).\n"
        "- Do NOT use 'all of the above' or 'none of the above' anywhere.\n"
        "- Options must not overlap or contradict each other.\n"
        "- All four labels (A/B/C/D) must appear exactly once; option order "
        "may be shuffled in the user-facing UI."
    )


def option_shape_directive() -> str:
    """The exact JSON shape Rex must return — single source of truth."""
    return (
        "Return exactly this JSON shape — nothing else:\n"
        f"{OPTIONS_JSON_BLOCK}"
    )


__all__ = [
    "OPTIONS_JSON_BLOCK",
    "distractor_rules_directive",
    "option_mode_directive",
    "option_shape_directive",
    "OPTION_LABELS",
]