# Rex prompts — Python port of agents/prompts/rex.ts
#
# Phase 11: the JSON shape Rex must return now includes a `response_mode`,
# `options` (exactly 4 labeled A/B/C/D), and `answer_key` (1 or 2 correct
# labels). The mode is app-controlled — callers pass it in. The opt-in
# directives live in `rex_options.py` so this file stays under the 200-line
# hard rule.

MODEL = "anthropic/claude-sonnet-4.6"

REX_SYSTEM = """You are Rex — a relentless AI adversary built to expose gaps in certification knowledge. You do not hand-hold. You do not soften questions. You challenge.

You generate scenario-based exam questions for the active certification, grounded in real operational situations — not trivia. Every challenge puts the user in the seat of an engineer making a real architectural or operational decision on that specific exam.

You respond ONLY with valid JSON. No preamble. No explanation. No markdown fences. No trailing text. Just the raw JSON object."""


def build_rex_challenge_prompt(
    exam_id: str,
    domain: str,
    topic: str = "",
    difficulty: str = "medium",
    task_statement: str = "",
    services: list[str] | None = None,
    source_ids: list[str] | None = None,
    concept_id: str = "",
    learning_style: str = "",
    familiarity_level: str = "new",
    facts: list[str] | None = None,
    traps: list[str] | None = None,
    response_mode: str = "single_response",
) -> tuple[str, str]:
    """Returns (system, user) prompt tuple for a new challenge.

    ``facts`` and ``traps`` are the selected concept's ground-truth claims and
    gotchas. ``response_mode`` is the app-controlled mode for this prompt
    (single_response | multiple_response). The Rex prompt instructs the LLM
    to emit a matching `answer_key`.
    """
    topic_instruction = (
        f'Target the selected concept/topic: "{topic}". Do not choose outside it.'
        if topic else
        "Use only the selected domain/task/source context. Do not invent unsupported topics."
    )
    context = _source_context(task_statement, services, source_ids, concept_id)
    facts_block = _facts_block(facts)
    traps_block = _traps_block(traps)
    style_directive = _style_directive(learning_style)
    familiarity_directive = _familiarity_directive(familiarity_level)
    from prompts.rex_options import (
        distractor_rules_directive,
        option_mode_directive,
        option_shape_directive,
    )
    options_block = (
        option_mode_directive(response_mode)
        + "\n"
        + distractor_rules_directive()
        + "\n"
        + option_shape_directive()
    )
    user = f"""Generate a {exam_id.upper()} challenge for the "{domain}" domain at {difficulty} difficulty.
{topic_instruction}
{context}
{facts_block}
{traps_block}
{style_directive}
{familiarity_directive}
{options_block}"""
    return REX_SYSTEM, user


def build_rex_rechallenge_prompt(
    exam_id: str,
    domain: str,
    concept_id: str = "",
    previous_topic: str = "",
    topic: str = "",
    difficulty: str = "hard",
    task_statement: str = "",
    services: list[str] | None = None,
    source_ids: list[str] | None = None,
    learning_style: str = "",
    familiarity_level: str = "new",
    facts: list[str] | None = None,
    traps: list[str] | None = None,
    response_mode: str = "single_response",
) -> tuple[str, str]:
    """Returns (system, user) prompt tuple for a harder rechallenge."""
    topic_instruction = (
        f'Target the selected next concept/topic: "{topic}". Do not choose outside it.'
        if topic else
        "Use only the selected next concept packet. Do not invent unsupported topics."
    )
    context = _source_context(task_statement, services, source_ids, concept_id)
    facts_block = _facts_block(facts)
    traps_block = _traps_block(traps)
    style_directive = _style_directive(learning_style, rechallenge=True)
    familiarity_directive = _familiarity_directive(familiarity_level)
    from prompts.rex_options import (
        distractor_rules_directive,
        option_mode_directive,
        option_shape_directive,
    )
    options_block = (
        option_mode_directive(response_mode)
        + "\n"
        + distractor_rules_directive()
        + "\n"
        + option_shape_directive()
    )
    user = f"""The challenger just saw Sage explain "{previous_topic}" in the "{domain}" domain. Now raise the stakes.

Generate a harder {exam_id.upper()} challenge on the SAME domain — different topic, selected next concept only, higher-pressure scenario, more nuanced question. Difficulty: {difficulty}.
{topic_instruction}
{context}
{facts_block}
{traps_block}
{style_directive}
{familiarity_directive}
{options_block}"""
    return REX_SYSTEM, user


def _style_directive(learning_style: str, rechallenge: bool = False) -> str:
    """Append a style-specific Rex directive. Empty string for mixed_review/""."""
    if learning_style == "pressure_drills":
        return (
            "Style: pressure_drills. Production-scale stakes — call out platform "
            "limits, throttling, ambiguity, and failure modes. Hard time or load "
            "constraints. No safety nets. Demand exact product names and "
            "operational detail. The user is being tested, not tutored."
        )
    if learning_style == "guided_explanations":
        if rechallenge:
            return (
                "Style: guided_explanations. Keep the rechallenge grounded — the "
                "user is still learning. Advance one new wrinkle beyond "
                "previous_topic, not three. Don't trap."
            )
        return (
            "Style: guided_explanations. Grounded scenario, one decision at a "
            "time. Lead the question so the user can reason through it. Do not "
            "trap. The point is to teach, not to catch them out."
        )
    return ""


def _familiarity_directive(familiarity_level: str) -> str:
    if familiarity_level == "new":
        return "Familiarity: new. Use one core decision and avoid unnecessary multi-service traps unless the selected style explicitly raises pressure."
    if familiarity_level == "building":
        return "Familiarity: building. Test the core rule plus one realistic wrinkle."
    return "Familiarity: review. The user has prior signal here; normal exam nuance is fair game."


def _source_context(
    task_statement: str,
    services: list[str] | None,
    source_ids: list[str] | None,
    concept_id: str = "",
) -> str:
    lines = []
    if task_statement:
        lines.append(f'Official task statement: "{task_statement}".')
    if services:
        lines.append(f"Use these services or concepts as context: {', '.join(services)}.")
    if source_ids:
        lines.append(f"Source IDs for traceability: {', '.join(source_ids)}.")
    if concept_id:
        lines.append(f"Selected concept ID: {concept_id}.")
    return "\n".join(lines)


def _facts_block(facts: list[str] | None) -> str:
    """Inline concept facts as ground-truth anchors Rex must respect."""
    if not facts:
        return ""
    bullet = "\n".join(f"- {item}" for item in facts)
    return (
        "Ground-truth facts about the selected concept — your scenario and "
        "question MUST be consistent with these:\n"
        f"{bullet}"
    )


def _traps_block(traps: list[str] | None) -> str:
    """Inline concept traps; Rex must NOT contradict or trivially leak these."""
    if not traps:
        return ""
    bullet = "\n".join(f"- {item}" for item in traps)
    return (
        "Known traps/misconceptions for this concept — your scenario must NOT "
        "answer the question for the user, and the question must not be trivially "
        "solvable by spotting the trap directly:\n"
        f"{bullet}"
    )