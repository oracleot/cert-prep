// Sage agent prompts — Phase 1
// Two paths: depth (correct) and explain (incorrect)
// Model: anthropic/claude-sonnet-4.6 via OpenRouter

export const MODEL = "anthropic/claude-sonnet-4.6";

const SAGE_SYSTEM = `You are Sage — the counterpoint to Rex. Where Rex attacks, you illuminate.

Your voice: dry wit, hard-won confidence. You never lecture. You never hedge. You never say "great job" or "good question". You never soften a gap. You cite AWS services, documentation, and concepts directly.

You are not here to comfort. You are here to make this person dangerous with this knowledge.`;

export type SageInput = {
  domain: string;
  topic: string;
  scenario: string;
  question: string;
  userAnswer: string;
  reasoning: string;
};

export function buildSageDepthPrompt(input: SageInput): {
  system: string;
  user: string;
} {
  return {
    system: SAGE_SYSTEM,
    user: `Topic: ${input.topic} (${input.domain})

The challenge:
${input.scenario}
${input.question}

They answered: "${input.userAnswer}"
Evaluator note: ${input.reasoning}

They got it right. Now go deeper. What else is worth knowing about this topic that the question didn't test? What separates a 750 from an 850 on this domain? Cite the specific AWS behaviour, edge case, or gotcha that most developers miss. Be specific. Be direct. Be useful.`,
  };
}

export function buildSageExplainPrompt(input: SageInput): {
  system: string;
  user: string;
} {
  return {
    system: SAGE_SYSTEM,
    user: `Topic: ${input.topic} (${input.domain})

The challenge:
${input.scenario}
${input.question}

They answered: "${input.userAnswer}"
The gap: ${input.reasoning}

Correct the misconception. Cite the specific AWS service or concept directly. Tell them exactly what the right mental model is and why it matters in a real deployment. No hedging. No "it depends". Give them the knowledge they were missing.`,
  };
}
