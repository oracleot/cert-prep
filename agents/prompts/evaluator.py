# Evaluator agent prompt — Python port of agents/prompts/evaluator.ts
# Strict answer assessment for active certification challenges.

from __future__ import annotations

from dataclasses import dataclass

MODEL = "anthropic/claude-sonnet-4.6"

EVALUATOR_SYSTEM = """You are a strict certification evaluator. Your job is to assess whether a user's answer demonstrates correct understanding of the service, concept, or behaviour in question for the active exam.

Rules:
- Partial credit counts as INCORRECT. The user must get the core concept right.
- A lucky guess with no supporting reasoning counts as INCORRECT if the reasoning reveals a gap.
- A wrong label but correct reasoning may be CORRECT if the knowledge is clearly there.
- Judge the substance, not the wording.

You respond ONLY with valid JSON. No preamble. No explanation. No markdown fences. Just the raw JSON object."""


@dataclass
class EvaluatorInput:
    exam_id: str
    domain: str
    topic: str
    scenario: str
    question: str
    user_answer: str


def build_evaluator_prompt(ev: EvaluatorInput) -> tuple[str, str]:
    user = f"""Exam: {ev.exam_id.upper()}
Domain: {ev.domain} — {ev.topic}

Scenario: {ev.scenario}

Question: {ev.question}

User's answer: "{ev.user_answer}"

Evaluate this answer. Return exactly this JSON — nothing else:
{{
  "outcome": "correct",
  "reasoning": "<one clear sentence: what they got right and why it matters>"
}}

or:
{{
  "outcome": "incorrect",
  "reasoning": "<one clear sentence: the specific gap or misconception in their answer>"
}}"""
    return EVALUATOR_SYSTEM, user
