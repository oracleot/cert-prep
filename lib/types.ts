// Shared domain types for Phase 1 Rex + Sage loop

export type Challenge = {
  domain: string;
  topic: string;
  scenario: string;
  question: string;
};

export type EvaluationResult = {
  outcome: "correct" | "incorrect";
  reasoning: string;
};

export type SessionResult = {
  cycle: number;
  topic: string;
  outcome: "correct" | "incorrect";
};
