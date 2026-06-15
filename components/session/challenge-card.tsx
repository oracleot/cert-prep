"use client";

// Challenge card — renders Rex's scenario and question
// AC 1.4: domain tag, topic tag, scenario, question; loading skeleton

import type { Challenge } from "@/lib/types";

type Props = {
  challenge: Challenge | null;
  isLoading: boolean;
};

export function ChallengeCard({ challenge, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-6 animate-pulse">
        <div className="mb-4 flex gap-2">
          <div className="h-5 w-20 rounded-full bg-muted" />
          <div className="h-5 w-28 rounded-full bg-muted" />
        </div>
        <div className="space-y-2">
          <div className="h-4 w-full rounded bg-muted" />
          <div className="h-4 w-5/6 rounded bg-muted" />
          <div className="h-4 w-4/6 rounded bg-muted" />
        </div>
        <div className="mt-4 h-px w-full bg-border" />
        <div className="mt-4 space-y-2">
          <div className="h-4 w-full rounded bg-muted" />
          <div className="h-4 w-3/4 rounded bg-muted" />
        </div>
      </div>
    );
  }

  if (!challenge) return null;

  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <div className="mb-4 flex flex-wrap gap-2">
        <span className="rounded-full bg-primary/10 px-3 py-0.5 text-xs font-semibold uppercase tracking-wide text-primary">
          {challenge.domain}
        </span>
        <span className="rounded-full bg-secondary px-3 py-0.5 text-xs font-medium text-secondary-foreground">
          {challenge.topic}
        </span>
      </div>

      <p className="text-sm leading-relaxed text-muted-foreground">
        {challenge.scenario}
      </p>

      <div className="my-4 h-px w-full bg-border" />

      <p className="text-base font-medium leading-snug text-foreground">
        {challenge.question}
      </p>
    </div>
  );
}
