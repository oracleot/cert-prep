"use client";

import type { Challenge, EvaluationResult, OptionLabel } from "@/lib/types";
import { OPTION_LABELS, isOptionLabel, normalizeOptionLabels } from "@/lib/types";

type Props = {
  challenge: Challenge | null;
  isLoading: boolean;
  // Phase 11 — option verdict overlay. When provided, each option is
  // marked with the corresponding visual state (chosen / correct / missed
  // / incorrect). The submitter (page.tsx) wires this from the active
  // EvaluationResult.
  verdict?: EvaluationResult | null;
  // Phase 11 — selection + lock state for the option controls. When the
  // challenge is option-based, the card renders 4 option rows and reflects
  // the user's selection + lock state.
  selectedLabels?: OptionLabel[];
  isLocked?: boolean;
  onToggleLabel?: (label: OptionLabel) => void;
};

function optionStatus(
  label: OptionLabel,
  verdict: EvaluationResult | null | undefined,
  selected: OptionLabel[],
): "default" | "chosen" | "correct" | "missed" | "incorrect" {
  if (!verdict) {
    if (selected.includes(label)) return "chosen";
    return "default";
  }
  const isCorrect = verdict.correct_labels?.includes(label) ?? false;
  const isMissed = verdict.missed_labels?.includes(label) ?? false;
  const isIncorrect = verdict.incorrect_labels?.includes(label) ?? false;
  const isChosen = verdict.selected_labels?.includes(label) ?? false;
  if (isCorrect && isChosen) return "correct";
  if (isCorrect && isMissed) return "missed";
  if (isIncorrect) return "incorrect";
  if (isChosen) return "correct"; // single-response: chosen = correct
  return "default";
}

const STATUS_STYLES: Record<ReturnType<typeof optionStatus>, string> = {
  default:
    "border-zinc-200 bg-white text-zinc-900 hover:border-amber-300/70 dark:border-zinc-800 dark:bg-zinc-950/70 dark:text-zinc-50",
  chosen:
    "border-amber-300 bg-amber-300/15 text-zinc-950 dark:border-amber-300 dark:bg-amber-300/10 dark:text-zinc-50",
  correct:
    "border-emerald-500 bg-emerald-500/15 text-emerald-900 dark:border-emerald-400 dark:bg-emerald-500/10 dark:text-emerald-100",
  missed:
    "border-rose-400 bg-rose-400/15 text-rose-900 dark:border-rose-400 dark:bg-rose-500/10 dark:text-rose-100",
  incorrect:
    "border-rose-500 bg-rose-500/15 text-rose-900 dark:border-rose-400 dark:bg-rose-500/10 dark:text-rose-100",
};

const STATUS_LABEL: Record<ReturnType<typeof optionStatus>, string> = {
  default: "",
  chosen: "Selected",
  correct: "Correct",
  missed: "Missed",
  incorrect: "Incorrect",
};

export function ChallengeCard({ challenge, isLoading, verdict = null, selectedLabels = [], isLocked = false, onToggleLabel }: Props) {
  if (isLoading) {
    return (
      <div className="rounded-2xl border border-zinc-200 bg-white/85 p-6 animate-pulse backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-950/80">
        <div className="mb-4 flex gap-2">
          <div className="h-5 w-20 rounded-full bg-zinc-200 dark:bg-zinc-800" />
          <div className="h-5 w-28 rounded-full bg-zinc-200 dark:bg-zinc-800" />
        </div>
        <div className="space-y-2">
          <div className="h-4 w-full rounded bg-zinc-200 dark:bg-zinc-800" />
          <div className="h-4 w-5/6 rounded bg-zinc-200 dark:bg-zinc-800" />
          <div className="h-4 w-4/6 rounded bg-zinc-200 dark:bg-zinc-800" />
        </div>
        <div className="mt-4 h-px w-full bg-zinc-200 dark:bg-zinc-800" />
        <div className="mt-4 space-y-2">
          <div className="h-4 w-full rounded bg-zinc-200 dark:bg-zinc-800" />
          <div className="h-4 w-3/4 rounded bg-zinc-200 dark:bg-zinc-800" />
        </div>
      </div>
    );
  }

  if (!challenge) return null;
  const difficulty = challenge.difficulty ?? "medium";
  const options = Array.isArray(challenge.options) && challenge.options.length === OPTION_LABELS.length
    ? challenge.options
    : null;
  const normalizedSelected = normalizeOptionLabels(selectedLabels);
  const isMulti = challenge.response_mode === "multiple_response";
  const showVerdict = Boolean(verdict);
  const allowToggle = Boolean(onToggleLabel) && !isLocked && !showVerdict;

  return (
    <div className="rounded-2xl border border-zinc-200 bg-white/85 p-6 backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-950/80">
      <div className="mb-4 flex flex-wrap gap-2">
        <span className="rounded-full border border-zinc-300 px-3 py-0.5 text-xs font-semibold uppercase tracking-wider text-zinc-600 dark:border-zinc-700 dark:text-zinc-300">
          {challenge.topic}
        </span>
        <span className="rounded-full border border-sky-300 bg-sky-300/10 px-3 py-0.5 text-xs font-semibold uppercase tracking-wider text-sky-700 dark:border-sky-700 dark:text-sky-300">
          {difficulty}
        </span>
        {challenge.familiarity_level === "new" && (
          <span className="rounded-full border border-amber-300 bg-amber-300/15 px-3 py-0.5 text-xs font-semibold uppercase tracking-wider text-amber-800 dark:border-amber-300">
            New domain ramp
          </span>
        )}
        {options && (
          <span className="rounded-full border border-zinc-300 bg-zinc-100 px-3 py-0.5 text-xs font-semibold uppercase tracking-wider text-zinc-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200">
            {isMulti ? "Select TWO" : "Select ONE"}
          </span>
        )}
      </div>

      <p className="text-sm leading-relaxed text-zinc-600 dark:text-zinc-300">
        {challenge.scenario}
      </p>

      <div className="my-4 h-px w-full bg-zinc-200 dark:bg-zinc-800" />

      <p className="text-base font-medium leading-snug text-zinc-950 dark:text-zinc-50">
        {challenge.question}
      </p>

      {options ? (
        <ul className="mt-4 space-y-2" aria-label="Answer options">
          {options.map((opt, idx) => {
            const rawLabel = opt?.label ?? OPTION_LABELS[idx];
            const label = isOptionLabel(rawLabel) ? rawLabel : OPTION_LABELS[idx];
            const text = typeof opt?.text === "string" ? opt.text : "";
            const status = optionStatus(label, verdict, normalizedSelected);
            return (
              <li key={label}>
                <button
                  type="button"
                  onClick={() => allowToggle && onToggleLabel?.(label)}
                  disabled={!allowToggle}
                  aria-pressed={normalizedSelected.includes(label)}
                  className={`flex w-full items-start gap-3 rounded-xl border px-3 py-2 text-left text-sm transition disabled:cursor-not-allowed ${STATUS_STYLES[status]}`}
                >
                  <span className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-[0.7rem] font-black ${
                    normalizedSelected.includes(label)
                      ? "border-amber-300 bg-amber-300 text-zinc-950"
                      : "border-zinc-300 text-zinc-700 dark:border-zinc-700 dark:text-zinc-300"
                  }`}>
                    {label}
                  </span>
                  <span className="flex-1 leading-snug">{text}</span>
                  {STATUS_LABEL[status] && (
                    <span className="ml-2 shrink-0 rounded-full border border-current/40 px-2 py-0.5 text-[0.6rem] font-semibold uppercase tracking-wider opacity-80">
                      {STATUS_LABEL[status]}
                    </span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}