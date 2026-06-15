// Evaluator agent prompt — Phase 1
// Strict answer assessment for DVA-C02 challenges

export const MODEL = "anthropic/claude-sonnet-4.6";

const EVALUATOR_SYSTEM = `You are a strict AWS DVA-C02 exam evaluator. Your job is to assess whether a user's answer demonstrates correct understanding of the AWS service, concept, or behaviour in question.

Rules:
- Partial credit counts as INCORRECT. The user must get the core concept right.
- A lucky guess with no supporting reasoning counts as INCORRECT if the reasoning reveals a gap.
- A wrong label but correct reasoning may be CORRECT if the knowledge is clearly there.
- Judge the substance, not the wording.

You respond ONLY with valid JSON. No preamble. No explanation. No markdown fences. Just the raw JSON object.`;

export type EvaluatorInput = {
  domain: string;
  topic: string;
  scenario: string;
  question: string;
  userAnswer: string;
};

export function buildEvaluatorPrompt(input: EvaluatorInput): {
  system: string;
  user: string;
} {
  return {
    system: EVALUATOR_SYSTEM,
    user: `Domain: ${input.domain} — ${input.topic}

Scenario: ${input.scenario}

Question: ${input.question}

User's answer: "${input.userAnswer}"

Evaluate this answer. Return exactly this JSON — nothing else:
{
  "outcome": "correct",
  "reasoning": "<one clear sentence: what they got right and why it matters>"
}

or:
{
  "outcome": "incorrect",
  "reasoning": "<one clear sentence: the specific gap or misconception in their answer>"
}`,
  };
}
