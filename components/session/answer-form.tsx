"use client";

// Answer form — text input + submit
// AC 1.4: submit disabled until user has typed something; evaluating state

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
        className="min-h-[120px] w-full resize-none rounded-lg border border-input bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
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
        className="w-full"
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
