# Rex prompts — Python port of agents/prompts/rex.ts

MODEL = "anthropic/claude-sonnet-4.6"

REX_SYSTEM = """You are Rex — a relentless AI adversary built to expose gaps in AWS knowledge. You do not hand-hold. You do not soften questions. You challenge.

You generate scenario-based AWS DVA-C02 exam questions grounded in real operational situations — not trivia. Every challenge puts the user in the seat of a developer making a real architectural or operational decision.

You respond ONLY with valid JSON. No preamble. No explanation. No markdown fences. No trailing text. Just the raw JSON object."""


def build_rex_challenge_prompt(
    domain: str,
    topic: str = "",
    difficulty: str = "medium",
) -> tuple[str, str]:
    """Returns (system, user) prompt tuple for a new challenge."""
    topic_instruction = f'Target topic: "{topic}".' if topic else "Choose a specific topic."
    user = f"""Generate a DVA-C02 challenge for the "{domain}" domain at {difficulty} difficulty.
{topic_instruction}

Return exactly this JSON shape — nothing else:
{{
  "domain": "{domain}",
  "topic": "{topic or '<specific topic within the domain>'}",
  "scenario": "<2-4 sentence operational scenario a developer would actually face>",
  "question": "<precise question about what the developer should do or what will happen>"
}}"""
    return REX_SYSTEM, user


def build_rex_rechallenge_prompt(
    domain: str, previous_topic: str, difficulty: str = "hard"
) -> tuple[str, str]:
    """Returns (system, user) prompt tuple for a harder rechallenge."""
    user = f"""The challenger just saw Sage explain "{previous_topic}" in the "{domain}" domain. Now raise the stakes.

Generate a harder challenge on the SAME domain — different topic, higher-pressure scenario, more nuanced question. Difficulty: {difficulty}.

Return exactly this JSON shape — nothing else:
{{
  "domain": "{domain}",
  "topic": "<different specific topic within {domain}>",
  "scenario": "<2-4 sentence scenario with higher stakes and less obvious answer>",
  "question": "<harder, more nuanced question — avoid yes/no, demand specific AWS knowledge>"
}}"""
    return REX_SYSTEM, user
