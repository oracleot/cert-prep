"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import type { SessionResult } from "@/lib/types";

type Props = {
  results: SessionResult[];
  domain: string;
  onRestart: () => void;
};

export function SummaryScreen({ results, domain, onRestart }: Props) {
  const correct = results.filter((r) => r.outcome === "correct").length;
  const total = results.length;
  const allCorrect = correct === total;

  return (
    <div className="flex flex-col gap-5">
      <div className="rounded-2xl border border-amber-300/30 bg-amber-300 p-6 text-center text-zinc-950">
        <p className="text-xs font-black uppercase tracking-[0.35em]">
          Session complete
        </p>

        <p className="mt-4 text-6xl font-black tabular-nums">
          {correct}
          <span className="text-2xl font-bold opacity-60">/{total}</span>
        </p>

        <p className="mt-3 text-sm font-semibold">
          {allCorrect
            ? "Rex had nothing on you today."
            : correct === 0
              ? "Rex won this one. Come back ready."
              : "You got some. Rex got some. Not done yet."}
        </p>
      </div>

      <div className="rounded-2xl border border-zinc-200 bg-white/85 p-5 backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-950/80">
        <p className="mb-3 text-xs font-semibold uppercase tracking-[0.35em] text-zinc-600 dark:text-zinc-500">
          Domain covered
        </p>
        <p className="text-sm font-bold text-zinc-950 dark:text-zinc-50">{domain}</p>

        <div className="mt-3 space-y-2">
          {results.map((r, i) => (
            <div key={i} className="flex items-center justify-between text-sm">
              <span className="text-zinc-600 dark:text-zinc-500">Cycle {r.cycle}</span>
              <span className="truncate px-2 text-zinc-700 dark:text-zinc-200">{r.topic}</span>
              <span
                className={
                  r.outcome === "correct"
                    ? "font-bold text-emerald-600 dark:text-emerald-300"
                    : "text-zinc-600 dark:text-zinc-500"
                }
              >
                {r.outcome === "correct" ? "✓" : "✗"}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <Button
          onClick={onRestart}
          className="w-full min-h-11 bg-amber-300 text-zinc-950 hover:bg-amber-200"
        >
          Start another session
        </Button>
        <Button
          asChild
          variant="outline"
          className="w-full min-h-11 border-zinc-300 bg-transparent text-zinc-700 hover:bg-zinc-100 hover:text-zinc-950 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
        >
          <Link href="/dashboard">Back to dashboard</Link>
        </Button>
      </div>
    </div>
  );
}
