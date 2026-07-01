"use client";
// Phase 11 — option-based session selection state.
//
// Keeps the option-selection state machine out of `use-session.ts` so the
// main session hook stays under the 200-line hard rule. The hook returns
// memoized `selectedLabels`, `toggleLabel`, and helpers to reset the
// selection for the next challenge.

import { useCallback, useState } from "react";
import type { Challenge, OptionLabel } from "@/lib/types";
import { OPTION_LABELS, normalizeOptionLabels } from "@/lib/types";

export type OptionSelectionHelpers = {
  selectedLabels: OptionLabel[];
  isOptionBased: boolean;
  isSubmitted: boolean;
  selectionError: string;
  canSubmit: boolean;
  toggleLabel: (label: OptionLabel) => void;
  clearSelection: () => void;
  markSubmitted: () => void;
  resetForNewChallenge: (next: Challenge | null) => void;
  selectedCsv: string;
};

const SINGLE_HINT = "Pick exactly one option.";
const MULTI_HINT_PREFIX = "Pick all that apply";

export function useOptionSelection(challenge: Challenge | null, isLocked: boolean): OptionSelectionHelpers {
  const [selected, setSelected] = useState<OptionLabel[]>([]);
  const [submitted, setSubmitted] = useState(false);

  const isOptionBased = Boolean(
    challenge?.options && challenge.options.length === OPTION_LABELS.length,
  );
  const mode = challenge?.response_mode ?? "";

  const toggle = useCallback(
    (label: OptionLabel) => {
      if (!isOptionBased || isLocked || submitted) return;
      setSelected((prev) => {
        const has = prev.includes(label);
        if (mode === "single_response") {
          // Single-response: only one label at a time. Selecting the already-
          // selected label keeps it (so the user can re-confirm).
          return has ? [label] : [label];
        }
        // Multi-response: 1-2 labels in V1.
        if (has) return prev.filter((l) => l !== label);
        if (prev.length >= 2) return prev;
        return normalizeOptionLabels([...prev, label]);
      });
    },
    [isOptionBased, isLocked, submitted, mode],
  );

  const clearSelection = useCallback(() => setSelected([]), []);
  const markSubmitted = useCallback(() => setSubmitted(true), []);

  const resetForNewChallenge = useCallback(
    () => {
      setSelected([]);
      setSubmitted(false);
    },
    [],
  );

  const has = selected.length > 0;
  const tooMany = mode === "multiple_response" && selected.length > 2;
  const selectionError = !has
    ? (mode === "single_response" ? SINGLE_HINT : `${MULTI_HINT_PREFIX} (1–2).`)
    : tooMany
      ? "Too many options selected — pick at most 2."
      : "";

  const canSubmit = isOptionBased
    ? has && !tooMany && !submitted
    : false;

  const selectedCsv = selected.join(",");

  return {
    selectedLabels: selected,
    isOptionBased,
    isSubmitted: submitted,
    selectionError,
    canSubmit,
    toggleLabel: toggle,
    clearSelection,
    markSubmitted,
    resetForNewChallenge,
    selectedCsv,
  };
}