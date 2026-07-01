"use client";

import { SummaryScreen } from "@/components/session/summary-screen";
import type { SessionResult } from "@/lib/types";

const BG_GRADIENT = "pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(251,191,36,0.18),transparent_32%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.12),transparent_32%)] dark:bg-[radial-gradient(circle_at_20%_10%,rgba(251,191,36,0.18),transparent_32%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.14),transparent_32%)]";

export function SessionSummaryView({
  results,
  domain,
  onRestart,
}: {
  results: SessionResult[];
  domain: string;
  onRestart: () => void;
}) {
  return (
    <main className="relative min-h-screen overflow-hidden bg-background px-4 py-12 text-foreground">
      <div className={BG_GRADIENT} />
      <div className="relative mx-auto flex w-full max-w-lg items-start justify-center">
        <SummaryScreen results={results} domain={domain} onRestart={onRestart} />
      </div>
    </main>
  );
}

export function SessionErrorView({ errorMsg, onRetry }: { errorMsg: string; onRetry: () => void }) {
  return (
    <main className="relative min-h-screen overflow-hidden bg-background px-4 text-foreground">
      <div className={BG_GRADIENT} />
      <div className="relative flex min-h-screen items-center justify-center">
        <div className="w-full max-w-lg rounded-2xl border border-rose-500/30 bg-rose-500/5 p-6 text-center backdrop-blur-sm">
          <p className="text-sm font-medium text-rose-700 dark:text-rose-200">{errorMsg}</p>
          <button
            onClick={onRetry}
            className="mt-4 min-h-11 rounded-full bg-amber-300 px-5 text-sm font-black text-zinc-950 hover:bg-amber-200"
          >
            Retry
          </button>
        </div>
      </div>
    </main>
  );
}