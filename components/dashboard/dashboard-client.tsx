"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppNav } from "@/components/navigation/app-nav";
import { getAnonymousUserId } from "@/lib/anonymous-user";
import type { DashboardSummary, DomainPlan } from "@/lib/types";

function DomainTile({ domain }: { domain: DomainPlan }) {
  return (
    <div className="rounded-3xl border border-zinc-800 bg-zinc-950 p-5">
      <div className="flex items-center justify-between gap-4">
        <h2 className="font-black text-zinc-50">{domain.name}</h2>
        <span className="text-sm font-black text-amber-300">{domain.weight}%</span>
      </div>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-zinc-800">
        <div
          className="h-full rounded-full bg-amber-300"
          style={{ width: `${domain.completion_percent || 0}%` }}
        />
      </div>
      <p className="mt-3 text-sm text-zinc-400">
        {domain.correct_count || 0}/{domain.total_count || 0} against Rex
      </p>
    </div>
  );
}

export function DashboardClient() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      const userId = getAnonymousUserId();
      const res = await fetch("/api/dashboard/summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId }),
      });
      if (!res.ok) {
        setError("Dashboard is waiting for the agent service.");
        return;
      }
      setSummary(await res.json());
    }

    void load();
  }, []);

  if (error) {
    return <main className="min-h-screen bg-black p-6 text-amber-200">{error}</main>;
  }

  if (!summary) {
    return <main className="min-h-screen bg-black p-6 text-zinc-400">Loading dashboard...</main>;
  }

  return (
    <main className="min-h-screen bg-black px-4 py-6 text-zinc-50 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <AppNav />
        <section className="mt-8 grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-[2rem] border border-zinc-800 bg-zinc-950 p-7 sm:p-10">
            <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-300">
              Readiness score
            </p>
            <div className="mt-6 flex items-end gap-3">
              <span className="text-7xl font-black tracking-tighter sm:text-8xl">
                {summary.readiness_score}%
              </span>
              {summary.readiness_score === 0 ? (
                <span className="mb-3 rounded-full border border-zinc-700 px-3 py-1 text-xs font-bold text-zinc-400">
                  ghost baseline
                </span>
              ) : null}
            </div>
            <p className="mt-5 max-w-xl text-zinc-400">
              Weighted from domain performance: weight times correct challenge rate.
            </p>
          </div>
          <div className="rounded-[2rem] border border-zinc-800 bg-amber-300 p-7 text-zinc-950 sm:p-10">
            <p className="text-xs font-black uppercase tracking-[0.35em]">Today</p>
            <h1 className="mt-4 text-4xl font-black tracking-tight">
              {summary.today_domain}
            </h1>
            <p className="mt-3 text-sm font-semibold opacity-80">{summary.today_topic}</p>
            <Link
              href="/session"
              className="mt-8 inline-flex min-h-11 items-center rounded-full bg-zinc-950 px-5 text-sm font-black text-zinc-50"
            >
              Start your first session
            </Link>
          </div>
        </section>
        <section className="mt-5 grid gap-5 lg:grid-cols-[0.8fr_1.2fr]">
          <div className="rounded-[2rem] border border-zinc-800 bg-zinc-950 p-7">
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-zinc-500">
              Rex&apos;s record
            </p>
            <p className="mt-5 text-5xl font-black">
              {summary.rex_record.user_wins}-{summary.rex_record.rex_wins}
            </p>
            <p className="mt-3 text-sm font-semibold uppercase tracking-[0.25em] text-zinc-400">YOU vs REX</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {summary.domains.map((domain) => <DomainTile key={domain.name} domain={domain} />)}
          </div>
        </section>
      </div>
    </main>
  );
}
