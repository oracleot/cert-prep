from __future__ import annotations

import re

KNOWLEDGE_GAP_ANSWER = "I don't know yet."

_UNCERTAIN_PATTERNS = [
    re.compile(r"^no idea[.!]?$", re.I),
    re.compile(r"^i\s+don'?t\s+know\s+yet[.!]?$", re.I),
    re.compile(r"^i\s+don'?t\s+know[.!]?$", re.I),
    re.compile(r"^not\s+sure[.!]?$", re.I),
    re.compile(r"^unsure[.!]?$", re.I),
]


def normalize_answer_intent(user_answer: str, answer_intent: str = "attempt") -> str:
    if answer_intent == "knowledge_gap":
        return "knowledge_gap"
    answer = user_answer.strip()
    return "knowledge_gap" if any(pattern.match(answer) for pattern in _UNCERTAIN_PATTERNS) else "attempt"
