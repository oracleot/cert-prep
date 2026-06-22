"use client";

import { Button } from "@/components/ui/button";
import type { AnswerIntent, Citation, SageFeedback, SageFeedbackType } from "@/lib/types";
import { SageFeedbackControl } from "./sage-feedback-control";
import { MarkdownStream } from "./markdown-stream";

type Props = {
  text: string;
  citations: Citation[];
  isStreaming: boolean;
  outcome: "correct" | "incorrect" | null;
  answerIntent: AnswerIntent;
  cycle: number;
  maxCycles: number;
  feedback: SageFeedback | null;
  onNext: () => void;
  onFeedbackSubmit: (feedbackType: SageFeedbackType, comment: string) => Promise<void>;
};

export function SageCard({
  text,
  citations,
  isStreaming,
  outcome,
  answerIntent,
  cycle,
  maxCycles,
  feedback,
  onNext,
  onFeedbackSubmit,
}: Props) {
  if (!text && !isStreaming) return null;

  const isLastCycle = cycle >= maxCycles;
  const isKnowledgeGap = answerIntent === "knowledge_gap";

  return (
    <div
      className={`rounded-2xl border p-6 backdrop-blur-sm ${
        outcome === "correct"
          ? "border-emerald-500/30 bg-emerald-500/10"
          : "border-zinc-200 bg-white/85 dark:border-zinc-800 dark:bg-zinc-950/80"
      }`}
    >
      <div className="mb-3 flex items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-[0.35em] text-zinc-600 dark:text-zinc-500">
          Sage
        </span>
        {outcome && (
          <span
            className={`text-xs font-semibold uppercase tracking-wider ${
              outcome === "correct"
                ? "text-emerald-600 dark:text-emerald-300"
                : isKnowledgeGap
                  ? "text-amber-700 dark:text-amber-300"
                : "text-zinc-500 dark:text-zinc-400"
            }`}
          >
            {outcome === "correct" ? "correct" : isKnowledgeGap ? "knowledge gap" : "incorrect"}
          </span>
        )}
      </div>

      <div className="relative text-sm leading-relaxed text-zinc-900 dark:text-zinc-100">
        <MarkdownStream text={text} className="text-zinc-100" />
        {isStreaming && (
          <span className="ml-0.5 inline-block h-4 w-px animate-pulse bg-zinc-900 align-middle dark:bg-zinc-100" />
        )}
      </div>

      {!isStreaming && citations.length > 0 && (
        <div className="mt-4 rounded-xl border border-zinc-200 bg-white/60 p-3 dark:border-zinc-800 dark:bg-zinc-900/60">
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.3em] text-zinc-500">
            Sources
          </p>
          <div className="mt-2 space-y-2">
            {citations.map((citation) => (
              <a
                key={`${citation.snippet_id}-${citation.url}`}
                href={citation.url}
                target="_blank"
                rel="noreferrer"
                className="block rounded-lg border border-transparent px-2 py-1 text-xs font-medium text-zinc-700 underline-offset-4 hover:border-amber-300/50 hover:text-zinc-950 hover:underline dark:text-zinc-300 dark:hover:text-amber-100"
              >
                {citation.title}
              </a>
            ))}
          </div>
        </div>
      )}

      {!isStreaming && text && (
        <SageFeedbackControl feedback={feedback} onSubmit={onFeedbackSubmit} />
      )}

      {!isStreaming && text && (
        <div className="mt-4 border-t border-zinc-200 pt-4 dark:border-zinc-800">
          <Button
            onClick={onNext}
            variant={isLastCycle ? "default" : "outline"}
            className={`w-full min-h-11 ${
              isLastCycle
                ? "bg-amber-300 text-zinc-950 hover:bg-amber-200"
                : "border-zinc-300 bg-transparent text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-100 dark:hover:bg-zinc-800"
            }`}
          >
            {isLastCycle ? "View session summary" : "Next challenge →"}
          </Button>
        </div>
      )}
    </div>
  );
}
