"use client";

import { Button } from "@/components/ui/button";

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  isDisabled: boolean;
  isEvaluating: boolean;
};

export function AnswerForm({
  value,
  onChange,
  onSubmit,
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
        className="min-h-[120px] w-full resize-none rounded-2xl border border-zinc-800 bg-zinc-950/80 px-4 py-3 text-sm text-zinc-50 placeholder:text-zinc-500 focus:border-amber-300 focus:outline-none focus:ring-2 focus:ring-amber-300/40 disabled:cursor-not-allowed disabled:opacity-50 backdrop-blur-sm"
        placeholder="Your answer… (⌘↵ to submit)"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={isDisabled}
        aria-label="Your answer"
      />

      <Button
        onClick={onSubmit}
        disabled={!canSubmit}
        className="w-full min-h-11 bg-amber-300 text-zinc-950 hover:bg-amber-200"
        aria-label={isEvaluating ? "Evaluating…" : "Submit answer"}
      >
        {isEvaluating ? (
          <span className="flex items-center gap-2">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
            Evaluating…
          </span>
        ) : (
          "Submit"
        )}
      </Button>
    </div>
  );
}
