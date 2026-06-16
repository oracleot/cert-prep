"use client";

import { useEffect, useState } from "react";
import { Lock } from "lucide-react";

import { AppNav } from "@/components/navigation/app-nav";
import { getAnonymousUserId } from "@/lib/anonymous-user";
import type { DomainPlan, TopicPlan } from "@/lib/types";

function toTopic(topic: string | TopicPlan): TopicPlan {
  return typeof topic === "string" ? { id: topic, name: topic } : topic;
}

export function ProgressClient() {
  const [domains, setDomains] = useState<DomainPlan[]>([]);

  useEffect(() => {
    async function load() {
      const userId = getAnonymousUserId();
      const res = await fetch("/api/progress", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId }),
      });
      if (res.ok) {
        const data = await res.json();
        setDomains(data.domains || []);
      }
    }

    void load();
  }, []);

  return (
    <main className="min-h-screen bg-background px-4 py-6 text-foreground sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <AppNav />
        <section className="mt-10 rounded-[2rem] border border-zinc-200 bg-white p-7 sm:p-10 dark:border-zinc-800 dark:bg-zinc-950">
          <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-600 dark:text-amber-300">
            Progress map
          </p>
          <h1 className="mt-4 text-4xl font-black tracking-tight sm:text-6xl">
            Full blueprint. No hiding.
          </h1>
          <div className="mt-8 grid gap-4">
            {domains.map((domain) => {
              const completion = domain.completion_percent || 0;
              return (
                <div key={domain.name} className="rounded-3xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-black/60">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h2 className="text-xl font-black">{domain.name}</h2>
                      <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">Weight {domain.weight}%</p>
                    </div>
                    <span className="rounded-full bg-zinc-100 px-3 py-1 text-sm font-black text-zinc-700 dark:bg-zinc-900 dark:text-zinc-300">
                      {completion === 0 ? (
                        <span className="inline-flex items-center gap-1">
                          <Lock aria-hidden="true" className="size-3" /> locked
                        </span>
                      ) : `${completion}%`}
                    </span>
                  </div>
                  <div className="mt-5 h-3 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
                    <div className="h-full bg-amber-300" style={{ width: `${completion}%` }} />
                  </div>
                  <div className="mt-5 grid gap-2 sm:grid-cols-2">
                    {domain.topics.map((rawTopic) => {
                      const topic = toTopic(rawTopic);
                      const covered = topic.status === "covered";
                      const label = topic.status === "in_progress" ? "in progress" : covered ? "covered" : "untouched";
                      return (
                        <div
                          key={topic.id}
                          className="rounded-2xl border border-zinc-200 bg-zinc-50 p-3 dark:border-zinc-800 dark:bg-zinc-950"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <p className="text-sm font-bold leading-snug">{topic.name}</p>
                            <span className={covered
                              ? "rounded-full bg-emerald-100 px-2 py-1 text-[0.65rem] font-black uppercase tracking-wide text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                              : "rounded-full bg-zinc-200 px-2 py-1 text-[0.65rem] font-black uppercase tracking-wide text-zinc-600 dark:bg-zinc-900 dark:text-zinc-400"
                            }>
                              {label}
                            </span>
                          </div>
                          <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
                            Task {topic.task_statement_id || "n/a"} · {(topic.services || []).slice(0, 2).join(", ") || "source mapped"}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </main>
  );
}
