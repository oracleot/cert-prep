"use client";

import { Button } from "@/components/ui/button";
import { MarkdownStream } from "./markdown-stream";

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
      className={`rounded-2xl border p-6 backdrop-blur-sm ${
        outcome === "correct"
          ? "border-emerald-400/30 bg-emerald-500/10"
          : "border-zinc-800 bg-zinc-950/80"
      }`}
    >
      <div className="mb-3 flex items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-[0.35em] text-zinc-500">
          Sage
        </span>
        {outcome && (
          <span
            className={`text-xs font-semibold uppercase tracking-wider ${
              outcome === "correct"
                ? "text-emerald-300"
                : "text-zinc-400"
            }`}
          >
            {outcome === "correct" ? "correct" : "incorrect"}
          </span>
        )}
      </div>

      <div className="relative text-sm leading-relaxed text-zinc-100">
        <MarkdownStream text={text} className="text-zinc-100" />
        {isStreaming && (
          <span className="ml-0.5 inline-block h-4 w-px animate-pulse bg-zinc-100 align-middle" />
        )}
      </div>

      {!isStreaming && text && (
        <div className="mt-4 border-t border-zinc-800 pt-4">
          <Button
            onClick={onNext}
            variant={isLastCycle ? "default" : "outline"}
            className={`w-full min-h-11 ${
              isLastCycle
                ? "bg-amber-300 text-zinc-950 hover:bg-amber-200"
                : "border-zinc-700 bg-transparent text-zinc-100 hover:bg-zinc-800"
            }`}
          >
            {isLastCycle ? "View session summary" : "Next challenge →"}
          </Button>
        </div>
      )}
    </div>
  );
}
