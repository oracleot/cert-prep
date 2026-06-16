# Rex prompts — Python port of agents/prompts/rex.ts

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
    learning_style: str = "",
) -> tuple[str, str]:
    """Returns (system, user) prompt tuple for a new challenge."""
    topic_instruction = f'Target topic: "{topic}".' if topic else "Choose a specific topic."
    context = _source_context(task_statement, services, source_ids)
    style_directive = _style_directive(learning_style)
    user = f"""Generate a {exam_id.upper()} challenge for the "{domain}" domain at {difficulty} difficulty.
{topic_instruction}
{context}
{style_directive}

Return exactly this JSON shape — nothing else:
{{
  "domain": "{domain}",
  "topic": "{topic or '<specific topic within the domain>'}",
  "scenario": "<2-4 sentence operational scenario an engineer would actually face>",
  "question": "<precise question about what the engineer should do or what will happen>"
}}"""
    return REX_SYSTEM, user


def build_rex_rechallenge_prompt(
    exam_id: str,
    domain: str,
    previous_topic: str,
    topic: str = "",
    difficulty: str = "hard",
    task_statement: str = "",
    services: list[str] | None = None,
    source_ids: list[str] | None = None,
    learning_style: str = "",
) -> tuple[str, str]:
    """Returns (system, user) prompt tuple for a harder rechallenge."""
    topic_instruction = f'Target the next topic: "{topic}".' if topic else "Choose a different specific topic."
    context = _source_context(task_statement, services, source_ids)
    style_directive = _style_directive(learning_style, rechallenge=True)
    user = f"""The challenger just saw Sage explain "{previous_topic}" in the "{domain}" domain. Now raise the stakes.

Generate a harder {exam_id.upper()} challenge on the SAME domain — higher-pressure scenario, more nuanced question. Difficulty: {difficulty}.
{topic_instruction}
{context}
{style_directive}

Return exactly this JSON shape — nothing else:
{{
  "domain": "{domain}",
  "topic": "{topic or f'<different specific topic within {domain}>'}",
  "scenario": "<2-4 sentence scenario with higher stakes and less obvious answer>",
  "question": "<harder, more nuanced question — avoid yes/no, demand specific exam knowledge>"
}}"""
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


def _source_context(
    task_statement: str,
    services: list[str] | None,
    source_ids: list[str] | None,
) -> str:
    lines = []
    if task_statement:
        lines.append(f'Official task statement: "{task_statement}".')
    if services:
        lines.append(f"Use these services or concepts as context: {', '.join(services)}.")
    if source_ids:
        lines.append(f"Source IDs for traceability: {', '.join(source_ids)}.")
    return "\n".join(lines)
