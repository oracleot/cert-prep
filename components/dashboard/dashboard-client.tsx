"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppNav } from "@/components/navigation/app-nav";
import { FocusDomainPicker } from "@/components/dashboard/focus-domain-picker";
import { getAnonymousUserId } from "@/lib/anonymous-user";
import { useActiveCurriculum } from "@/lib/active-curriculum";
import { getBrowserTimezone } from "@/lib/browser-timezone";
import { clearThreadId, loadThreadId } from "@/app/session/session-persistence";
import type { DashboardSummary, DomainPlan } from "@/lib/types";

function formatPercent(value: number) {
  return Number.isInteger(value) ? value.toString() : value.toFixed(2).replace(/\.?0+$/, "");
}

function DomainTile({ domain }: { domain: DomainPlan }) {
  const covered = domain.covered_topic_count || 0;
  const topicCount = domain.topic_count || domain.topics.length;
  return (
    <div className="rounded-3xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
      <div className="flex items-center justify-between gap-4">
        <h2 className="font-black text-zinc-950 dark:text-zinc-50">{domain.name}</h2>
        <span className="text-sm font-black text-amber-600 dark:text-amber-300">{domain.weight}%</span>
      </div>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
        <div
          className="h-full rounded-full bg-amber-500 dark:bg-amber-300"
          style={{ width: `${domain.completion_percent || 0}%` }}
        />
      </div>
      <p className="mt-3 text-sm text-zinc-500 dark:text-zinc-400">
        {covered}/{topicCount} topics covered - {domain.correct_count || 0}/{domain.total_count || 0} vs Rex
      </p>
      <p className="mt-2 text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400 dark:text-zinc-500">
        {domain.weight}% weight x {formatPercent(domain.performance_score * 100)}% topic mastery = {formatPercent(domain.readiness_contribution || 0)}%
      </p>
    </div>
  );
}

type CtaState = "first" | "resume" | "another";

function resolveCtaState(
  summary: DashboardSummary,
  hasInProgressThread: boolean,
): CtaState {
  if (hasInProgressThread) return "resume";
  const totalPlayed =
    summary.rex_record.user_wins + summary.rex_record.rex_wins;
  if (totalPlayed === 0) return "first";
  return "another";
}

const CTA_COPY: Record<CtaState, string> = {
  first: "Start your first session",
  resume: "Resume session",
  another: "Start another session",
};

export function DashboardClient() {
  const { active } = useActiveCurriculum();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState("");
  const [focusDomain, setFocusDomain] = useState("");
  const [hasInProgressThread, setHasInProgressThread] = useState<boolean>(() => Boolean(loadThreadId()));

  function endSession() {
    clearThreadId();
    setHasInProgressThread(false);
  }

  useEffect(() => {
    async function load() {
      const userId = getAnonymousUserId();
      const res = await fetch("/api/dashboard/summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, exam_id: active?.exam_id ?? "", timezone: getBrowserTimezone() }),
      });
      if (!res.ok) {
        setError("Dashboard is waiting for the agent service.");
        return;
      }
      setSummary(await res.json());
    }

    void load();
  }, [active?.exam_id]);

  if (error) {
    return <main className="min-h-screen bg-background p-6 text-amber-700 dark:text-amber-200">{error}</main>;
  }

  if (!summary) {
    return <main className="min-h-screen bg-background p-6 text-muted-foreground">Loading dashboard...</main>;
  }

  const ctaState = resolveCtaState(summary, hasInProgressThread);
  const hasFocus = Boolean(focusDomain) && !hasInProgressThread;
  const ctaLabel = hasFocus ? "Start focused session" : CTA_COPY[ctaState];
  const sessionHref = hasFocus ? `/session?focus_domain=${encodeURIComponent(focusDomain)}` : "/session";

  return (
    <main className="min-h-screen bg-background px-4 py-6 text-foreground sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <AppNav />
        <section className="mt-8 grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
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
          <div className="rounded-[2rem] border border-zinc-800 bg-amber-300 p-7 text-zinc-950 sm:p-10">
            <p className="text-xs font-black uppercase tracking-[0.35em]">{hasFocus ? "Focus drill" : "Next up"}</p>
            <h1 className="mt-4 text-4xl font-black tracking-tight">
              {hasFocus ? focusDomain : summary.today_domain}
            </h1>
            <p className="mt-3 text-sm font-semibold opacity-80">
              {hasFocus ? "Rex will pick a weak or uncovered topic in this domain." : summary.today_topic}
            </p>
            <FocusDomainPicker
              domains={summary.domains}
              value={focusDomain}
              disabled={hasInProgressThread}
              onChange={setFocusDomain}
            />
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href={sessionHref}
                className="inline-flex min-h-11 items-center rounded-full bg-zinc-950 px-5 text-sm font-black text-zinc-50 dark:bg-zinc-950"
              >
                {ctaLabel}
              </Link>
              {hasInProgressThread ? (
                <button
                  type="button"
                  onClick={endSession}
                  className="min-h-11 rounded-full border border-zinc-950/30 px-5 text-sm font-black text-zinc-950 hover:border-zinc-950"
                >
                  End session
                </button>
              ) : null}
            </div>
          </div>
        </section>
        <section className="mt-5 grid gap-5 lg:grid-cols-2">
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
          <div className="grid gap-3 sm:grid-cols-2 lg:col-span-2">
            {summary.domains.map((domain) => <DomainTile key={domain.name} domain={domain} />)}
          </div>
        </section>
      </div>
    </main>
  );
}
