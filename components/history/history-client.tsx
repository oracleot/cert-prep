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
  const [selectedId, setSelectedId] = useState<string | null>(null);
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

  async function selectSession(id: string) {
    setSelectedId(id);
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

  const selectedItem = items?.find((item) => item.id === selectedId) || null;
  const selectedDetail = selectedId ? details[selectedId] : null;

  if (error) {
    return <main className="min-h-screen bg-background p-6 text-amber-700 dark:text-amber-200">{error}</main>;
  }
  if (!items) {
    return <main className="min-h-screen bg-background p-6 text-muted-foreground">Loading history...</main>;
  }

  return (
    <main className="min-h-screen bg-background px-4 py-6 text-foreground sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
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
          <section className="mt-8 grid gap-5 lg:grid-cols-[minmax(260px,1fr)_3fr] lg:gap-0">
            <aside className="overflow-hidden rounded-[2rem] border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-950 lg:max-h-[calc(100vh-15rem)] lg:overflow-y-auto lg:rounded-r-none">
              <div className="px-2 pb-3 pt-2">
                <p className="text-xs font-black uppercase tracking-[0.3em] text-zinc-500 dark:text-zinc-400">
                  Sessions
                </p>
              </div>
              <div className="grid gap-2">
                {items.map((item) => {
                  const isSelected = selectedId === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => selectSession(item.id)}
                      className={
                        isSelected
                          ? "block w-full min-w-0 rounded-3xl border border-zinc-900 bg-zinc-950 p-4 text-left text-zinc-50 dark:border-amber-300 dark:bg-amber-300 dark:text-zinc-950"
                          : "block w-full min-w-0 rounded-3xl border border-transparent p-4 text-left hover:bg-zinc-100 dark:hover:bg-zinc-900"
                      }
                      aria-pressed={isSelected}
                    >
                      <div className="min-w-0">
                        <p className={isSelected
                          ? "text-xs font-semibold uppercase tracking-[0.25em] opacity-70"
                          : "text-xs font-semibold uppercase tracking-[0.25em] text-zinc-500 dark:text-zinc-400"
                        }>
                          {item.started_at ? new Date(item.started_at).toLocaleString() : "Unknown date"}
                        </p>
                        <h2 className="mt-2 truncate text-base font-black">{item.domain}</h2>
                        <p className={isSelected
                          ? "mt-1 line-clamp-2 text-sm opacity-80"
                          : "mt-1 line-clamp-2 text-sm text-zinc-500 dark:text-zinc-400"
                        }>
                          {item.topic}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>
            </aside>
            <section className="min-h-[28rem] rounded-[2rem] border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950 sm:p-7 lg:rounded-l-none lg:border-l-0">
              {!selectedId ? (
                <div className="flex min-h-[22rem] items-center justify-center rounded-3xl border border-dashed border-zinc-200 p-8 text-center dark:border-zinc-800">
                  <div>
                    <p className="text-xs font-black uppercase tracking-[0.35em] text-amber-600 dark:text-amber-300">
                      Session reader
                    </p>
                    <h2 className="mt-4 text-3xl font-black tracking-tight">Pick a session</h2>
                    <p className="mt-3 max-w-md text-sm text-zinc-500 dark:text-zinc-400">
                      Select a past run on the left to review Rex&apos;s challenge, your answer, and Sage&apos;s explanation.
                    </p>
                  </div>
                </div>
              ) : loadingId === selectedId || !selectedDetail ? (
                <p className="text-sm text-zinc-500 dark:text-zinc-400">Loading exchanges...</p>
              ) : (
                <div>
                  <div className="mb-5 border-b border-zinc-200 pb-5 dark:border-zinc-800">
                    <p className="text-xs font-semibold uppercase tracking-[0.3em] text-zinc-500 dark:text-zinc-400">
                      {selectedItem?.started_at
                        ? new Date(selectedItem.started_at).toLocaleString()
                        : "Unknown date"}
                    </p>
                    <div className="mt-3 flex flex-wrap items-end justify-between gap-3">
                      <div>
                        <h2 className="text-3xl font-black tracking-tight">
                          {selectedDetail.domain}
                        </h2>
                        <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
                          {selectedDetail.topic}
                        </p>
                      </div>
                      <div className="rounded-2xl bg-zinc-100 px-4 py-3 text-right dark:bg-zinc-900">
                        <p className="text-3xl font-black">
                          {selectedItem?.correct_count}/{selectedItem?.total_cycles}
                        </p>
                        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-zinc-500 dark:text-zinc-400">
                          vs Rex
                        </p>
                      </div>
                    </div>
                  </div>
                  <SessionDetail detail={selectedDetail} />
                </div>
              )}
            </section>
          </section>
        )}
      </div>
    </main>
  );
}
