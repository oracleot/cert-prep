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
    # Phase 9.5 — concept packet resources (verified by the curator). Sage
    # must only cite URLs drawn from these lists; no invented/fallback URLs.
    official_docs: list[str] | None = None
    skill_builder_links: list[str] | None = None
    lab_links: list[str] | None = None
    # Phase 11 — option-based session context. When set, Sage is told to refer
    # to options by label + short paraphrase, and to explicitly call out missed
    # correct options / incorrectly chosen options on multi-response misses.
    response_mode: str = ""
    options: list[dict] | None = None
    answer_key: list[str] | None = None
    selected_labels: list[str] | None = None
    missed_labels: list[str] | None = None
    incorrect_labels: list[str] | None = None


def _grounding_rules(sage: SageInput) -> str:
    if sage.has_verified_sources:
        return """Use the verified sources below for any source-backed claim.
Do not invent citations or URLs. Do not paste raw URLs inline; citation links render below the response.
Only cite URLs that appear in the verified source material — do not invent or guess any link.
If a claim is not backed by a verified source, say so rather than naming an unverified doc.
Mention at least one source title naturally when it supports the explanation."""
    return """No verified source was available for this topic.
Begin exactly with "Unverified explanation:". Do not invent citations, URLs, or documentation names.
Do not invent or guess any URL — leave citations empty rather than fabricate one."""


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


def _short_paraphrase(text: str, limit: int = 60) -> str:
    """First sentence / first 60 chars of an option for label-reference style."""
    if not text:
        return ""
    snippet = text.strip().split(".")[0].strip()
    if len(snippet) > limit:
        snippet = snippet[: limit - 1].rstrip() + "…"
    return snippet


def _option_directive(sage: SageInput) -> str:
    """Phase 11 — option-aware Sage instructions.

    Injected whenever the challenge carries option data. Tells Sage to refer
    to options by label + short paraphrase, prioritize the correct option(s)
    deeply, cover distractors briefly, and on multi-response misses name the
    missed correct options and any incorrect selections explicitly.
    """
    options = sage.options or []
    if not options:
        return ""
    rows: list[str] = []
    for opt in options:
        if not isinstance(opt, dict):
            continue
        label = str(opt.get("label", "")).strip()
        text = str(opt.get("text", "")).strip()
        if not label or not text:
            continue
        rows.append(f"  - {label}: {_short_paraphrase(text)}")
    if not rows:
        return ""
    options_block = "\n".join(rows)
    selected = list(sage.selected_labels or [])
    missed = list(sage.missed_labels or [])
    incorrect = list(sage.incorrect_labels or [])
    is_multi = sage.response_mode == "multiple_response"

    parts: list[str] = ["Option contract:"]
    parts.append(f"- Mode: {sage.response_mode or 'unknown'}. Each label refers to:")
    parts.append(options_block)
    parts.append("- Refer to options by label (A/B/C/D) plus a short paraphrase of the option text — never repeat the option text verbatim.")
    parts.append("- Explain the correct option(s) first and in more depth.")
    parts.append("- Cover each distractor in one short sentence — the rule it appears to test and why it does not actually apply.")
    if selected:
        parts.append(f"- The learner selected: {', '.join(selected)}.")
    if missed:
        parts.append(
            f"- Multi-response miss: explicitly name the missed correct option(s) — {', '.join(missed)} — and explain why each is required."
        )
    if incorrect:
        parts.append(
            f"- The learner incorrectly chose: {', '.join(incorrect)}. Explain why each is wrong."
        )
    if is_multi:
        parts.append("- Because this is a multi-response prompt, walk through every label the learner picked AND every label they missed; never silently skip a label.")
    return "\n".join(parts)


def build_sage_depth_prompt(sage: SageInput) -> tuple[str, str]:
    style_line = _style_directive(sage.learning_style, "depth")
    style_block = f"\n{style_line}" if style_line else ""
    context_directive = _context_directive(sage)
    option_block = _option_directive(sage)
    option_section = f"\n{option_block}\n" if option_block else ""
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
{option_section}
They got it right. Now go deeper. What else is worth knowing about this topic that the question didn't test? What separates a 750 from an 850 on this domain? Cite the specific behaviour, edge case, or gotcha that most practitioners miss. Be specific. Be direct. Be useful.{style_block}"""
    return SAGE_SYSTEM, user


def build_sage_explain_prompt(sage: SageInput) -> tuple[str, str]:
    style_line = _style_directive(sage.learning_style, "explain")
    style_block = f"\n{style_line}" if style_line else ""
    context_directive = _context_directive(sage)
    option_block = _option_directive(sage)
    option_section = f"\n{option_block}\n" if option_block else ""
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
{option_section}
{instruction} No hedging. No "it depends". Give them the knowledge they were missing.{style_block}"""
    return SAGE_SYSTEM, user
