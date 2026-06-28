"use client";

import type { DashboardSummary } from "@/lib/types";

function formatPercent(value: number) {
  return Number.isInteger(value) ? value.toString() : value.toFixed(2).replace(/\.?0+$/, "");
}

// Hero "Readiness score" tile, extracted from dashboard-client.tsx so the
// dashboard stays under the 200-line hard rule while the Review Queue CTA
// is wired in.
export function ReadinessTile({ summary }: { summary: DashboardSummary }) {
  return (
    <div className="rounded-[2rem] border border-zinc-200 bg-white p-7 sm:p-10 dark:border-zinc-800 dark:bg-zinc-950">
      <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-600 dark:text-amber-300">
        Readiness score
      </p>
      <div className="mt-6 flex items-end gap-3">
        <span className="text-7xl font-black tracking-tighter sm:text-8xl">
          {formatPercent(summary.readiness_score)}%
        </span>
        {summary.readiness_score === 0 ? (
          <span className="mb-3 rounded-full border border-zinc-300 px-3 py-1 text-xs font-bold text-zinc-500 dark:border-zinc-700 dark:text-zinc-400">
            ghost baseline
          </span>
        ) : null}
      </div>
      <p className="mt-5 max-w-xl text-zinc-500 dark:text-zinc-400">
        Weighted from domain performance; coverage bars track blueprint topics actually answered correctly.
      </p>
    </div>
  );
}

// "Daily streak" + "Rex's record" stat tiles. The dashboard grid expects
// them as a fragment with two children so they sit in the first two
// grid-cols-2 slots before the domain-tile row spans both columns.
export function StatTiles({ summary }: { summary: DashboardSummary }) {
  return (
    <>
      <div className="rounded-[2rem] border border-zinc-200 bg-white p-7 dark:border-zinc-800 dark:bg-zinc-950">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-zinc-500 dark:text-zinc-500">
          Daily streak
        </p>
        <p className="mt-5 text-5xl font-black">{summary.streak.current_streak}</p>
        <p className="mt-3 text-sm font-semibold uppercase tracking-[0.25em] text-zinc-500 dark:text-zinc-400">
          completed-session days
        </p>
      </div>
      <div className="rounded-[2rem] border border-zinc-200 bg-white p-7 dark:border-zinc-800 dark:bg-zinc-950">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-zinc-500 dark:text-zinc-500">
          Rex&apos;s record
        </p>
        <p className="mt-5 text-5xl font-black">
          {summary.rex_record.user_wins}-{summary.rex_record.rex_wins}
        </p>
        <p className="mt-3 text-sm font-semibold uppercase tracking-[0.25em] text-zinc-500 dark:text-zinc-400">YOU vs REX</p>
      </div>
    </>
  );
}

// Convenience object so call sites can use either name explicitly.
export const DashboardSummaryCard = { ReadinessTile, StatTiles };
