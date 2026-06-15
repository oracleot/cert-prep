"use client";

// Sage response card — streams in token-by-token
// AC 1.7: distinct visual from Rex card, streams via SSE, correct/incorrect treatment, Next CTA

import { Button } from "@/components/ui/button";

type Props = {
  text: string;
  isStreaming: boolean;
  outcome: "correct" | "incorrect" | null;
  cycle: number;
  maxCycles: number;
  onNext: () => void;
};

export function SageCard({
  text,
  isStreaming,
  outcome,
  cycle,
  maxCycles,
  onNext,
}: Props) {
  if (!text && !isStreaming) return null;

  const isLastCycle = cycle >= maxCycles;

  return (
    <div
      className={`rounded-xl border p-6 ${
        outcome === "correct"
          ? "border-emerald-200 bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950/30"
          : "border-border bg-muted/40"
      }`}
    >
      <div className="mb-3 flex items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Sage
        </span>
        {outcome && (
          <span
            className={`text-xs font-medium ${
              outcome === "correct"
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-muted-foreground"
            }`}
          >
            {outcome === "correct" ? "correct" : "incorrect"}
          </span>
        )}
      </div>

      <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
        {text}
        {isStreaming && (
          <span className="inline-block h-4 w-px animate-pulse bg-foreground align-middle" />
        )}
      </p>

      {!isStreaming && text && (
        <div className="mt-4 border-t border-border pt-4">
          <Button
            onClick={onNext}
            variant={isLastCycle ? "default" : "outline"}
            className="w-full"
          >
            {isLastCycle ? "View session summary" : "Next challenge →"}
          </Button>
        </div>
      )}
    </div>
  );
}
