# Evaluator agent prompt — Python port of agents/prompts/evaluator.ts
# Strict answer assessment for active certification challenges.

from __future__ import annotations

from dataclasses import dataclass

MODEL = "anthropic/claude-haiku-4.5"

EVALUATOR_SYSTEM = """You are a strict certification evaluator. Your job is to assess whether a user's answer demonstrates correct understanding of the service, concept, or behaviour in question for the active exam.

Rules:
- Partial credit counts as INCORRECT. The user must get the core concept right.
- A lucky guess with no supporting reasoning counts as INCORRECT if the reasoning reveals a gap.
- A wrong label but correct reasoning may be CORRECT if the knowledge is clearly there.
- Judge the substance, not the wording.
- Always populate `missed_criteria` and `triggered_traps` lists (use [] when nothing applies). These drive the internal concept-miss audit; they are not shown to the user as a score.

You respond ONLY with valid JSON. No preamble. No explanation. No markdown fences. Just the raw JSON object."""


@dataclass
class EvaluatorInput:
    exam_id: str
    domain: str
    topic: str
    scenario: str
    question: str
    user_answer: str
    # Phase 9.4 — packet-grounded evaluator. expected_answer_criteria is the
    # concept's success criterion; traps are the gotchas to cross-reference.
    expected_answer_criteria: str = ""
    traps: list[str] | None = None


def build_evaluator_prompt(ev: EvaluatorInput) -> tuple[str, str]:
    criteria_block = ""
    if ev.expected_answer_criteria:
        criteria_block = (
            "\nExpected answer criteria (the bar for CORRECT):\n"
            f"{ev.expected_answer_criteria}\n"
        )
    traps_block = ""
    if ev.traps:
        bullet = "\n".join(f"- {item}" for item in ev.traps)
        traps_block = (
            "\nKnown traps / misconceptions for this concept — flag any the "
            "user stumbled into:\n"
            f"{bullet}\n"
        )
    user = f"""Exam: {ev.exam_id.upper()}
Domain: {ev.domain} — {ev.topic}

Scenario: {ev.scenario}

Question: {ev.question}

User's answer: "{ev.user_answer}"
{criteria_block}{traps_block}
Evaluate this answer. Return exactly this JSON — nothing else:
{{
  "outcome": "correct" | "incorrect",
  "reasoning": "<one clear sentence: what they got right or the specific gap>",
  "missed_criteria": ["<criterion from expected_answer_criteria the answer failed to satisfy>"],
  "triggered_traps": ["<trap from the trap list the user's answer stumbled into>"]
}}"""
    return EVALUATOR_SYSTEM, user
