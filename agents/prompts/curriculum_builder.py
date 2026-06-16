from __future__ import annotations

import json

MODEL = "anthropic/claude-sonnet-4.6"

SYSTEM = """You are the Curriculum Builder for Gauntlet. You create compact,
exam-relevant study sequences for the active certification. Return only valid JSON with no markdown."""


def build_curriculum_prompt(blueprint: list[dict], learning_style: str) -> tuple[str, str]:
    payload = json.dumps(blueprint, indent=2)
    user = f"""Create a personalised curriculum from this blueprint.

Learning style: {learning_style}
Blueprint: {payload}

Rules:
- Keep the same four domains and weights.
- Preserve every task_statement exactly as provided.
- Preserve every topic object exactly as provided, including id, name, task_statement_id, services, and source_ids.
- Do not summarize, merge, rename, remove, or add topics.
- Add study_order from 1 to 4.
- Put the best first domain for this learning style at study_order 1.
- Return exactly a JSON array of domain objects.

Shape:
[
  {{
    "name": "Deployment",
    "weight": 24,
    "task_statements": [{{"id": "...", "text": "..."}}],
    "topics": [{{"id": "...", "name": "...", "task_statement_id": "...", "services": ["..."], "source_ids": ["..."]}}],
    "study_order": 1,
    "performance_score": 0
  }}
]"""
    return SYSTEM, user
