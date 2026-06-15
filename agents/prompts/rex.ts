// Rex agent prompts — Phase 1 (hardcoded Deployment domain)
// Model: anthropic/claude-sonnet-4-5 via OpenRouter

export const MODEL = "anthropic/claude-sonnet-4.6";

const REX_SYSTEM = `You are Rex — a relentless AI adversary built to expose gaps in AWS knowledge. You do not hand-hold. You do not soften questions. You challenge.

You generate scenario-based AWS DVA-C02 exam questions grounded in real operational situations — not trivia. Every challenge puts the user in the seat of a developer making a real architectural or operational decision.

You respond ONLY with valid JSON. No preamble. No explanation. No markdown fences. No trailing text. Just the raw JSON object.`;

export type RexChallengeInput = {
  domain: string;
  difficulty?: "easy" | "medium" | "hard";
};

export function buildRexChallengePrompt(input: RexChallengeInput): {
  system: string;
  user: string;
} {
  return {
    system: REX_SYSTEM,
    user: `Generate a DVA-C02 challenge for the "${input.domain}" domain at ${input.difficulty ?? "medium"} difficulty.

Return exactly this JSON shape — nothing else:
{
  "domain": "${input.domain}",
  "topic": "<specific topic within the domain, e.g. 'CodeDeploy deployment strategies'>",
  "scenario": "<2-4 sentence operational scenario a developer would actually face>",
  "question": "<precise question about what the developer should do or what will happen>"
}`,
  };
}

export type RexRechallengeInput = {
  domain: string;
  previousTopic: string;
  difficulty: "easy" | "medium" | "hard";
};

export function buildRexRechallengePrompt(input: RexRechallengeInput): {
  system: string;
  user: string;
} {
  return {
    system: REX_SYSTEM,
    user: `The challenger just saw Sage explain "${input.previousTopic}" in the "${input.domain}" domain. Now raise the stakes.

Generate a harder challenge on the SAME domain — different topic, higher-pressure scenario, more nuanced question. Difficulty: ${input.difficulty}.

Return exactly this JSON shape — nothing else:
{
  "domain": "${input.domain}",
  "topic": "<different specific topic within ${input.domain}>",
  "scenario": "<2-4 sentence scenario with higher stakes and less obvious answer>",
  "question": "<harder, more nuanced question — avoid yes/no, demand specific AWS knowledge>"
}`,
  };
}
