// Rex agent prompts — Phase 1 (hardcoded Deployment domain)
// Model: anthropic/claude-sonnet-4-5 via OpenRouter

export const MODEL = "anthropic/claude-sonnet-4.6";

const REX_SYSTEM = `You are Rex — a relentless AI adversary built to expose gaps in certification knowledge. You do not hand-hold. You do not soften questions. You challenge.

You generate scenario-based certification exam questions grounded in real operational situations — not trivia. Every challenge puts the user in the seat of a practitioner making a real architectural or operational decision.

You respond ONLY with valid JSON. No preamble. No explanation. No markdown fences. No trailing text. Just the raw JSON object.`;

export type RexChallengeInput = {
  domain: string;
  difficulty?: "easy" | "medium" | "hard";
  task_statement?: string;
  services?: string[];
  source_ids?: string[];
  concept_id?: string;
};

export function buildRexChallengePrompt(input: RexChallengeInput): {
  system: string;
  user: string;
} {
  const sourceContext = _sourceContext(
    input.task_statement,
    input.services,
    input.source_ids,
    input.concept_id
  );
  return {
    system: REX_SYSTEM,
    user: `Generate a certification challenge for the "${input.domain}" domain at ${input.difficulty ?? "medium"} difficulty.${sourceContext ? `\n\nSource grounding:\n${sourceContext}` : ""}

Return exactly this JSON shape — nothing else:
{
  "domain": "${input.domain}",
  "topic": "<specific topic within the domain>",
  "scenario": "<2-4 sentence operational scenario a practitioner would actually face>",
  "question": "<precise question about what the practitioner should do or what will happen>"
}`,
  };
}

export type RexRechallengeInput = {
  domain: string;
  previousTopic: string;
  difficulty?: "easy" | "medium" | "hard";
  task_statement?: string;
  services?: string[];
  source_ids?: string[];
  concept_id?: string;
};

export function buildRexRechallengePrompt(input: RexRechallengeInput): {
  system: string;
  user: string;
} {
  const sourceContext = _sourceContext(
    input.task_statement,
    input.services,
    input.source_ids,
    input.concept_id
  );
  return {
    system: REX_SYSTEM,
    user: `The challenger just saw Sage explain "${input.previousTopic}" in the "${input.domain}" domain. Now raise the stakes.

Generate a harder challenge on the SAME domain — different topic, higher-pressure scenario, more nuanced question. Difficulty: ${input.difficulty ?? "medium"}.${sourceContext ? `\n\nSource grounding:\n${sourceContext}` : ""}

Return exactly this JSON shape — nothing else:
{
  "domain": "${input.domain}",
  "topic": "<different specific topic within ${input.domain}>",
  "scenario": "<2-4 sentence scenario with higher stakes and less obvious answer>",
  "question": "<harder, more nuanced question — avoid yes/no, demand specific exam knowledge>"
}`,
  };
}

function _sourceContext(
  task_statement?: string,
  services?: string[],
  source_ids?: string[],
  concept_id?: string
): string {
  const lines: string[] = [];
  if (concept_id) lines.push(`Concept ID for grounding: "${concept_id}".`);
  if (task_statement) lines.push(`Official task statement: "${task_statement}".`);
  if (services && services.length > 0)
    lines.push(`Use these services or concepts as context: ${services.join(", ")}.`);
  if (source_ids && source_ids.length > 0)
    lines.push(`Source IDs for traceability: ${source_ids.join(", ")}.`);
  return lines.join("\n");
}
