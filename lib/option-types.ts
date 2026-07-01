// Phase 11 — Option-based session types.
//
// Each Rex prompt is one of two response modes. Selection-only answering;
// verdict is binary (correct/incorrect) and exposed immediately so the UI
// can mark chosen / correct / missed / incorrect options before Sage streams.

export type ResponseMode = "single_response" | "multiple_response";

export type OptionLabel = "A" | "B" | "C" | "D";

export const OPTION_LABELS: readonly OptionLabel[] = ["A", "B", "C", "D"];

export type ChallengeOption = {
  label: OptionLabel;
  text: string;
};

export type OptionVerdict = {
  selected_labels: OptionLabel[];
  correct_labels: OptionLabel[];
  missed_labels: OptionLabel[];
  incorrect_labels: OptionLabel[];
};

export function isOptionLabel(value: unknown): value is OptionLabel {
  return value === "A" || value === "B" || value === "C" || value === "D";
}

export function normalizeOptionLabels(values: readonly unknown[]): OptionLabel[] {
  const out: OptionLabel[] = [];
  for (const value of values) {
    if (isOptionLabel(value) && !out.includes(value)) out.push(value);
  }
  out.sort();
  return out;
}

export function isResponseMode(value: unknown): value is ResponseMode {
  return value === "single_response" || value === "multiple_response";
}