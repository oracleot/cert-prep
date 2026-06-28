"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppNav } from "@/components/navigation/app-nav";
import { getAnonymousUserId } from "@/lib/anonymous-user";
import { useActiveCurriculum } from "@/lib/active-curriculum";

type DueItem = {
  concept_id: string;
  topic: string;
  domain: string;
  last_outcome: "correct" | "incorrect" | null;
  days_since_seen: number | null;
};

type QueueResponse = {
  due: DueItem[];
  total_due: number;
};

function OutcomeBadge({ outcome }: { outcome: DueItem["last_outcome"] }) {
  if (outcome === "correct") {
    return (
      <span className="rounded-full bg-emerald-100 px-3 py-1 text-[0.65rem] font-black uppercase tracking-wide text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
        last: correct
      </span>
    );
  }
  if (outcome === "incorrect") {
    return (
      <span className="rounded-full bg-rose-100 px-3 py-1 text-[0.65rem] font-black uppercase tracking-wide text-rose-700 dark:bg-rose-950 dark:text-rose-300">
        last: incorrect
      </span>
    );
  }
  return (
    <span className="rounded-full bg-zinc-200 px-3 py-1 text-[0.65rem] font-black uppercase tracking-wide text-zinc-600 dark:bg-zinc-900 dark:text-zinc-400">
      never seen
    </span>
  );
}

export function ReviewQueueClient() {
  const { active } = useActiveCurriculum();
  const examId = active?.exam_id ?? "dva-c02";
  const [data, setData] = useState<QueueResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      const userId = getAnonymousUserId();
      const res = await fetch("/api/review/queue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, exam_id: examId, limit: 10 }),
      });
      if (!res.ok) {
        setError("Review queue is waiting for the agent service.");
        return;
      }
      setData(await res.json());
    }
    void load();
  }, [examId]);

  if (error) {
    return (
      <main className="min-h-screen bg-background p-6 text-amber-700 dark:text-amber-200">{error}</main>
    );
  }
  if (!data) {
    return <main className="min-h-screen bg-background p-6 text-muted-foreground">Loading review queue...</main>;
  }

  return (
    <main className="min-h-screen bg-background px-4 py-6 text-foreground sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl">
        <AppNav />
        <section className="mt-10">
          <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-600 dark:text-amber-300">
            Review queue
          </p>
          <h1 className="mt-3 text-4xl font-black tracking-tight sm:text-6xl">
            Today&apos;s Review Queue — {data.total_due} due
          </h1>
          <p className="mt-3 text-zinc-500 dark:text-zinc-400">
            Concepts the spaced-repetition schedule says you&apos;re about to forget. Pick one to drill.
          </p>
        </section>
        {data.due.length === 0 ? (
          <section className="mt-12 flex min-h-[40vh] items-center justify-center rounded-[2rem] border border-zinc-200 bg-white p-10 text-center dark:border-zinc-800 dark:bg-zinc-950">
            <div>
              <p className="text-3xl">All caught up. ✅</p>
              <p className="mt-3 text-zinc-500 dark:text-zinc-400">Come back tomorrow.</p>
            </div>
          </section>
        ) : (
          <section className="mt-8 grid gap-4">
            {data.due.map((item) => (
              <Link
                key={item.concept_id}
                // Phase 10 — URL-driven entry into the session page so the
                // "review" mode + concept_id are threaded to /api/session/start.
                href={`/session?mode=review&concept_id=${encodeURIComponent(item.concept_id)}`}
                className="flex flex-wrap items-center justify-between gap-3 rounded-3xl border border-zinc-200 bg-white p-5 transition hover:border-amber-300 dark:border-zinc-800 dark:bg-zinc-950 dark:hover:border-amber-300"
              >
                <div className="min-w-0">
                  <p className="text-xs font-semibold uppercase tracking-[0.3em] text-zinc-500 dark:text-zinc-400">
                    {item.domain}
                  </p>
                  <h2 className="mt-1 text-xl font-black tracking-tight text-zinc-950 dark:text-zinc-50">
                    {item.topic}
                  </h2>
                  <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                    {item.days_since_seen === null
                      ? "first review"
                      : `last seen ${item.days_since_seen}d ago`}
                  </p>
                </div>
                <OutcomeBadge outcome={item.last_outcome} />
              </Link>
            ))}
          </section>
        )}
      </div>
    </main>
  );
}
