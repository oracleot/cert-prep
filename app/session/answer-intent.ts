import type { AnswerIntent } from "@/lib/types";

const UNCERTAIN_PATTERNS = [
  /^no idea[.!]?$/i,
  /^i\s+don'?t\s+know\s+yet[.!]?$/i,
  /^i\s+don'?t\s+know[.!]?$/i,
  /^not\s+sure[.!]?$/i,
  /^unsure[.!]?$/i,
];

export const KNOWLEDGE_GAP_ANSWER = "I don't know yet.";

export function answerIntentFor(text: string, intent: AnswerIntent = "attempt"): AnswerIntent {
  const trimmed = text.trim();
  if (intent === "knowledge_gap") return intent;
  return UNCERTAIN_PATTERNS.some((pattern) => pattern.test(trimmed)) ? "knowledge_gap" : "attempt";
}

export function answerTextFor(text: string, intent: AnswerIntent): string {
  return intent === "knowledge_gap" && !text.trim() ? KNOWLEDGE_GAP_ANSWER : text;
}
