"use client";

import { MarkdownStream } from "@/components/session/markdown-stream";
import type { Citation, SessionHistoryDetail } from "@/lib/types";

function CitationList({ citations }: { citations: Citation[] }) {
  if (!citations || citations.length === 0) return null;
  return (
    <ul className="mt-3 space-y-1">
      {citations.map((c, i) => (
        <li key={`${c.url}-${i}`} className="text-xs">
          <a
            href={c.url}
            target="_blank"
            rel="noreferrer"
            className="text-amber-700 underline underline-offset-2 hover:text-amber-600 dark:text-amber-300"
          >
            {c.title || c.url}
          </a>
        </li>
      ))}
    </ul>
  );
}

function ExchangeBlock({ exchange }: { exchange: SessionHistoryDetail["exchanges"][number] }) {
  const isCorrect = exchange.outcome === "correct";
  return (
    <div className="rounded-2xl border border-zinc-200 bg-zinc-50 p-5 dark:border-zinc-800 dark:bg-zinc-900/50">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-black uppercase tracking-[0.3em] text-zinc-500 dark:text-zinc-400">
          Cycle {exchange.cycle} - {exchange.domain} - {exchange.topic}
        </p>
        <span
          className={
            isCorrect
              ? "rounded-full bg-emerald-100 px-3 py-1 text-[0.65rem] font-black uppercase tracking-wide text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
              : "rounded-full bg-zinc-200 px-3 py-1 text-[0.65rem] font-black uppercase tracking-wide text-zinc-600 dark:bg-zinc-900 dark:text-zinc-400"
          }
        >
          {isCorrect ? "You won" : "Rex won"}
        </span>
      </div>
      <h3 className="mt-4 text-lg font-black tracking-tight">Rex&apos;s challenge</h3>
      <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-zinc-700 dark:text-zinc-200">
        {exchange.challenge.scenario}
      </p>
      <p className="mt-2 text-sm font-bold text-zinc-950 dark:text-zinc-50">
        {exchange.challenge.question}
      </p>
      <h3 className="mt-5 text-xs font-black uppercase tracking-[0.3em] text-zinc-500 dark:text-zinc-400">
        Your answer
      </h3>
      <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-zinc-700 dark:text-zinc-200">
        {exchange.user_answer || "(no answer recorded)"}
      </p>
      <h3 className="mt-5 text-xs font-black uppercase tracking-[0.3em] text-zinc-500 dark:text-zinc-400">
        Sage
      </h3>
      <div className="mt-2">
        <MarkdownStream text={exchange.sage_response} />
      </div>
      <CitationList citations={exchange.citations} />
    </div>
  );
}

export function SessionDetail({ detail }: { detail: SessionHistoryDetail }) {
  if (detail.exchanges.length === 0) {
    return (
      <p className="text-sm text-zinc-500 dark:text-zinc-400">
        This session has no completed exchanges yet.
      </p>
    );
  }
  return (
    <div className="grid gap-5">
      {detail.exchanges.map((ex) => (
        <ExchangeBlock key={ex.cycle} exchange={ex} />
      ))}
    </div>
  );
}
