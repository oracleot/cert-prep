"use client";

import type { Challenge } from "@/lib/types";

type Props = {
  challenge: Challenge | null;
  isLoading: boolean;
};

export function ChallengeCard({ challenge, isLoading }: Props) {
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

  return (
    <div className="rounded-2xl border border-zinc-200 bg-white/85 p-6 backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-950/80">
      <div className="mb-4 flex flex-wrap gap-2">
        <span className="rounded-full bg-amber-300/15 px-3 py-0.5 text-xs font-semibold uppercase tracking-wider text-amber-700 dark:text-amber-300">
          {challenge.domain}
        </span>
        <span className="rounded-full border border-zinc-300 px-3 py-0.5 text-xs font-semibold uppercase tracking-wider text-zinc-600 dark:border-zinc-700 dark:text-zinc-300">
          {challenge.topic}
        </span>
      </div>

      <p className="text-sm leading-relaxed text-zinc-600 dark:text-zinc-300">
        {challenge.scenario}
      </p>

      <div className="my-4 h-px w-full bg-zinc-200 dark:bg-zinc-800" />

      <p className="text-base font-medium leading-snug text-zinc-950 dark:text-zinc-50">
        {challenge.question}
      </p>
    </div>
  );
}
