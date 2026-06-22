# Sage agent prompts — Python port of agents/prompts/sage.ts
# Two paths: depth (correct) and explain (incorrect)
# Model: anthropic/claude-sonnet-4.6 via OpenRouter

from __future__ import annotations

from dataclasses import dataclass

MODEL = "anthropic/claude-sonnet-4.6"

SAGE_SYSTEM = """You are Sage — the counterpoint to Rex. Where Rex attacks, you illuminate.

Your voice: dry wit, hard-won confidence. You never lecture. You never hedge. You never say "great job" or "good question". You never soften a gap. You cite relevant services, documentation, and concepts directly.

You are not here to comfort. You are here to make this person dangerous with this knowledge."""


@dataclass
class SageInput:
    domain: str
    topic: str
    scenario: str
    question: str
    user_answer: str
    reasoning: str
    source_context: str
    has_verified_sources: bool
    learning_style: str = ""
    answer_intent: str = "attempt"
    familiarity_level: str = "new"


def _grounding_rules(sage: SageInput) -> str:
    if sage.has_verified_sources:
        return """Use the verified sources below for any source-backed claim.
Do not invent citations or URLs. Do not paste raw URLs inline; citation links render below the response.
Mention at least one source title naturally when it supports the explanation."""
    return """No verified source was available for this topic.
Begin exactly with "Unverified explanation:". Do not invent citations, URLs, or documentation names."""


def _style_directive(learning_style: str, kind: str) -> str:
    """Style-specific closing line for Sage. Empty for mixed_review / ""."""
    if learning_style == "pressure_drills":
        if kind == "depth":
            return "Style: pressure_drills. Lean into the gotchas, edge cases, and platform limits that bite under production pressure. The user asked for pressure — give them the things that burn senior engineers at 3am."
        return "Style: pressure_drills. Be terse and surgical. State the correct mental model in one pass. No filler, no preamble, no softening. The user wants the answer, not a debrief."
    if learning_style == "guided_explanations":
        if kind == "depth":
            return "Style: guided_explanations. Build from first principles. Walk through the underlying behaviour before adding depth — the user is still constructing the model, not stress-testing it."
        return "Style: guided_explanations. Diagnose the misconception step by step. Repair the mental model before naming the right answer. The user is learning, not being tested."
    return ""


def _context_directive(sage: SageInput) -> str:
    lines = [f"Familiarity: {sage.familiarity_level}."]
    if sage.answer_intent == "knowledge_gap":
        lines.append("They did not attempt an answer. Teach the foundation, then the exact exam rule, then one concrete AWS example. Do not diagnose a misconception.")
    elif sage.familiarity_level == "new":
        lines.append("Assume this is early exposure to the topic; make the mental model explicit before adding exam nuance.")
    return "\n".join(lines)


def build_sage_depth_prompt(sage: SageInput) -> tuple[str, str]:
    style_line = _style_directive(sage.learning_style, "depth")
    style_block = f"\n{style_line}" if style_line else ""
    context_directive = _context_directive(sage)
    user = f"""Topic: {sage.topic} ({sage.domain})

Grounding:
{_grounding_rules(sage)}

Source material:
{sage.source_context}

The challenge:
{sage.scenario}
{sage.question}

They answered: "{sage.user_answer}"
Evaluator note: {sage.reasoning}
{context_directive}

They got it right. Now go deeper. What else is worth knowing about this topic that the question didn't test? What separates a 750 from an 850 on this domain? Cite the specific behaviour, edge case, or gotcha that most practitioners miss. Be specific. Be direct. Be useful.{style_block}"""
    return SAGE_SYSTEM, user


def build_sage_explain_prompt(sage: SageInput) -> tuple[str, str]:
    style_line = _style_directive(sage.learning_style, "explain")
    style_block = f"\n{style_line}" if style_line else ""
    context_directive = _context_directive(sage)
    instruction = "Teach the missing foundation, state the exact exam rule, then give one concrete AWS example." if sage.answer_intent == "knowledge_gap" else "Correct the misconception. Cite the specific service or concept directly. Tell them exactly what the right mental model is and why it matters in a real deployment."
    user = f"""Topic: {sage.topic} ({sage.domain})

Grounding:
{_grounding_rules(sage)}

Source material:
{sage.source_context}

The challenge:
{sage.scenario}
{sage.question}

They answered: "{sage.user_answer}"
The gap: {sage.reasoning}
{context_directive}

{instruction} No hedging. No "it depends". Give them the knowledge they were missing.{style_block}"""
    return SAGE_SYSTEM, user
