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
    <div className="flex flex-col gap-6">
      <div className="rounded-xl border border-border bg-card p-6 text-center">
        <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Session complete
        </p>

        <p className="mt-3 text-5xl font-bold tabular-nums text-foreground">
          {correct}
          <span className="text-2xl font-normal text-muted-foreground">
            /{total}
          </span>
        </p>

        <p className="mt-2 text-sm text-muted-foreground">
          {allCorrect
            ? "Rex had nothing on you today."
            : correct === 0
              ? "Rex won this one. Come back ready."
              : "You got some. Rex got some. Not done yet."}
        </p>
      </div>

      <div className="rounded-xl border border-border bg-card p-4">
        <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Domain covered
        </p>
        <p className="text-sm font-medium text-foreground">{domain}</p>

        <div className="mt-3 space-y-2">
          {results.map((r, i) => (
            <div key={i} className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Cycle {r.cycle}</span>
              <span className="truncate px-2 text-foreground">{r.topic}</span>
              <span
                className={
                  r.outcome === "correct"
                    ? "font-medium text-emerald-600 dark:text-emerald-400"
                    : "text-muted-foreground"
                }
              >
                {r.outcome === "correct" ? "✓" : "✗"}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <Button onClick={onRestart} className="w-full min-h-11">
          Start another session
        </Button>
        <Button
          asChild
          variant="outline"
          className="w-full min-h-11 text-muted-foreground"
        >
          <Link href="/dashboard">Back to dashboard</Link>
        </Button>
      </div>
    </div>
  );
}
