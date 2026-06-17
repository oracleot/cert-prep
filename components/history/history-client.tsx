"use client";

import { useEffect, useState } from "react";

import { AppNav } from "@/components/navigation/app-nav";
import { getAnonymousUserId } from "@/lib/anonymous-user";
import type { SessionHistoryDetail, SessionHistoryItem } from "@/lib/types";

import { SessionDetail } from "./session-detail";

function EmptyHistory() {
  return (
    <section className="mt-10 rounded-[2rem] border border-zinc-200 bg-white p-10 text-center dark:border-zinc-800 dark:bg-zinc-950">
      <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-600 dark:text-amber-300">
        History
      </p>
      <h1 className="mt-4 text-3xl font-black tracking-tight sm:text-5xl">No sessions yet</h1>
      <p className="mt-4 text-zinc-500 dark:text-zinc-400">
        Complete a session and your past Rex challenges and Sage explanations show up here.
      </p>
    </section>
  );
}

export function HistoryClient() {
  const [items, setItems] = useState<SessionHistoryItem[] | null>(null);
  const [error, setError] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [details, setDetails] = useState<Record<string, SessionHistoryDetail>>({});
  const [loadingId, setLoadingId] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const userId = getAnonymousUserId();
      const res = await fetch("/api/history/list", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId }),
      });
      if (!res.ok) {
        setError("History is waiting for the agent service.");
        return;
      }
      const data = await res.json();
      setItems(data.sessions || []);
    }
    void load();
  }, []);

  async function toggle(id: string) {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    if (details[id]) return;
    setLoadingId(id);
    const userId = getAnonymousUserId();
    const res = await fetch("/api/history/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, session_id: id }),
    });
    if (res.ok) {
      const data: SessionHistoryDetail = await res.json();
      setDetails((prev) => ({ ...prev, [id]: data }));
    }
    setLoadingId(null);
  }

  if (error) {
    return (
      <main className="min-h-screen bg-background p-6 text-amber-700 dark:text-amber-200">
        {error}
      </main>
    );
  }
  if (!items) {
    return (
      <main className="min-h-screen bg-background p-6 text-muted-foreground">
        Loading history...
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background px-4 py-6 text-foreground sm:px-6 lg:px-8">
      <div className="mx-auto max-w-4xl">
        <AppNav />
        <section className="mt-10">
          <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-600 dark:text-amber-300">
            History
          </p>
          <h1 className="mt-3 text-4xl font-black tracking-tight sm:text-6xl">Past sessions</h1>
          <p className="mt-3 text-zinc-500 dark:text-zinc-400">
            Rex&apos;s challenge and Sage&apos;s explanation, preserved.
          </p>
        </section>
        {items.length === 0 ? (
          <EmptyHistory />
        ) : (
          <section className="mt-8 grid gap-4">
            {items.map((item) => {
              const isOpen = expandedId === item.id;
              const detail = details[item.id];
              return (
                <article
                  key={item.id}
                  className="rounded-3xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950"
                >
                  <button
                    onClick={() => toggle(item.id)}
                    className="flex w-full items-center justify-between gap-4 rounded-3xl p-5 text-left"
                    aria-expanded={isOpen}
                  >
                    <div className="min-w-0">
                      <p className="text-xs font-semibold uppercase tracking-[0.3em] text-zinc-500 dark:text-zinc-400">
                        {item.started_at
                          ? new Date(item.started_at).toLocaleString()
                          : "Unknown date"}
                      </p>
                      <h2 className="mt-1 truncate text-xl font-black">{item.domain}</h2>
                      <p className="mt-1 truncate text-sm text-zinc-500 dark:text-zinc-400">
                        {item.topic}
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      <p className="text-2xl font-black">
                        {item.correct_count}/{item.total_cycles}
                      </p>
                      <p className="text-xs font-semibold uppercase tracking-[0.25em] text-zinc-500 dark:text-zinc-400">
                        vs Rex
                      </p>
                    </div>
                  </button>
                  {isOpen ? (
                    <div className="border-t border-zinc-200 p-5 dark:border-zinc-800">
                      {loadingId === item.id || !detail ? (
                        <p className="text-sm text-zinc-500 dark:text-zinc-400">
                          Loading exchanges...
                        </p>
                      ) : (
                        <SessionDetail detail={detail} />
                      )}
                    </div>
                  ) : null}
                </article>
              );
            })}
          </section>
        )}
      </div>
    </main>
  );
}
