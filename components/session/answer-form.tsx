"use client";

import { Button } from "@/components/ui/button";

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  onKnowledgeGap: () => void;
  isDisabled: boolean;
  isEvaluating: boolean;
};

export function AnswerForm({
  value,
  onChange,
  onSubmit,
  onKnowledgeGap,
  isDisabled,
  isEvaluating,
}: Props) {
  const canSubmit = value.trim().length > 0 && !isDisabled;

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && canSubmit) {
      e.preventDefault();
      onSubmit();
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <textarea
        className="min-h-[120px] w-full resize-none rounded-2xl border border-zinc-300 bg-white/85 px-4 py-3 text-sm text-zinc-950 placeholder:text-zinc-400 focus:border-amber-300 focus:outline-none focus:ring-2 focus:ring-amber-300/40 disabled:cursor-not-allowed disabled:opacity-50 backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-950/80 dark:text-zinc-50 dark:placeholder:text-zinc-500"
        placeholder="Explain your answer, or type 'no idea' if you're stuck. (⌘↵ to submit)"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isDisabled}
        aria-label="Your answer"
      />

      <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
        <Button
          onClick={onSubmit}
          disabled={!canSubmit}
          className="min-h-11 bg-amber-300 text-zinc-950 hover:bg-amber-200"
          aria-label={isEvaluating ? "Evaluating…" : "Submit answer"}
        >
          {isEvaluating ? (
            <span className="flex items-center gap-2">
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
              Evaluating…
            </span>
          ) : "Submit"}
        </Button>
        <Button onClick={onKnowledgeGap} disabled={isDisabled} variant="outline" className="min-h-11 border-zinc-300 bg-white/70 text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:bg-transparent dark:text-zinc-200 dark:hover:bg-zinc-800">
          I don&apos;t know yet
        </Button>
      </div>
    </div>
  );
}
