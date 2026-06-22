"use client";

import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import type { SageFeedback, SageFeedbackType } from "@/lib/types";

const OPTIONS: Array<{ value: SageFeedbackType; label: string }> = [
  { value: "factual_error", label: "Hallucination / factually wrong" },
  { value: "bad_source", label: "Bad or missing source" },
  { value: "confusing_explanation", label: "Confusing explanation" },
];

type Props = {
  feedback: SageFeedback | null;
  onSubmit: (feedbackType: SageFeedbackType, comment: string) => Promise<void>;
};

export function SageFeedbackControl({ feedback, onSubmit }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [feedbackType, setFeedbackType] = useState<SageFeedbackType>("factual_error");
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (feedback) {
    return (
      <div className="mt-4 rounded-xl border border-amber-300/40 bg-amber-300/10 p-3 text-xs text-zinc-700 dark:text-zinc-200">
        <p className="font-black uppercase tracking-[0.22em] text-amber-700 dark:text-amber-300">Flagged for review</p>
        <p className="mt-1">
          {feedback.excludes_metrics ? "This cycle is excluded from your progress while pending review." : "Thanks, this will be reviewed."}
        </p>
      </div>
    );
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = comment.trim();
    if (trimmed.length < 10 || trimmed.length > 1000) {
      setError("Add 10 to 1000 characters so this is reviewable.");
      return;
    }
    setIsSubmitting(true); setError("");
    try {
      await onSubmit(feedbackType, trimmed);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Feedback failed to save. Try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!isOpen) {
    return (
      <Button type="button" variant="ghost" className="mt-4 min-h-10 px-0 text-xs font-bold text-zinc-500 hover:text-zinc-950 dark:text-zinc-400 dark:hover:text-zinc-100" onClick={() => setIsOpen(true)}>
        <span aria-hidden="true" className="mr-2">⚑</span> Flag issue
      </Button>
    );
  }

  return (
    <form onSubmit={submit} className="mt-4 rounded-xl border border-zinc-200 bg-white/60 p-3 dark:border-zinc-800 dark:bg-zinc-900/60">
      <label className="text-[0.65rem] font-black uppercase tracking-[0.25em] text-zinc-500" htmlFor="sage-feedback-type">Issue type</label>
      <select id="sage-feedback-type" value={feedbackType} onChange={(e) => setFeedbackType(e.target.value as SageFeedbackType)} className="mt-2 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950">
        {OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
      </select>
      <label className="mt-3 block text-[0.65rem] font-black uppercase tracking-[0.25em] text-zinc-500" htmlFor="sage-feedback-comment">What did Sage get wrong?</label>
      <textarea id="sage-feedback-comment" value={comment} onChange={(e) => setComment(e.target.value)} rows={3} maxLength={1000} className="mt-2 w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950" />
      {error && <p className="mt-2 text-xs font-semibold text-rose-600 dark:text-rose-300">{error}</p>}
      <div className="mt-3 flex gap-2">
        <Button type="submit" disabled={isSubmitting} className="min-h-10 bg-amber-300 text-zinc-950 hover:bg-amber-200">{isSubmitting ? "Submitting..." : "Submit flag"}</Button>
        <Button type="button" variant="outline" className="min-h-10" onClick={() => setIsOpen(false)}>Cancel</Button>
      </div>
    </form>
  );
}
