from __future__ import annotations

import json

MODEL = "anthropic/claude-sonnet-4.6"

SYSTEM = """You are the Curriculum Builder for Gauntlet. You create compact,
exam-relevant DVA-C02 study sequences. Return only valid JSON with no markdown."""


def build_curriculum_prompt(blueprint: list[dict], learning_style: str) -> tuple[str, str]:
    payload = json.dumps(blueprint, indent=2)
    user = f"""Create a personalised curriculum from this DVA-C02 blueprint.

Learning style: {learning_style}
Blueprint: {payload}

Rules:
- Keep the same four domains and weights.
- Preserve 3-5 high-value topics per domain.
- Add study_order from 1 to 4.
- Put the best first domain for this learning style at study_order 1.
- Return exactly a JSON array of domain objects.

Shape:
[
  {{
    "name": "Deployment",
    "weight": 32,
    "topics": ["..."],
    "study_order": 1,
    "performance_score": 0
  }}
]"""
    return SYSTEM, user
