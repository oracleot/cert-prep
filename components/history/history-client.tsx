"use client";

import { useCallback, useEffect, useState } from "react";

import { AppNav } from "@/components/navigation/app-nav";
import { getAnonymousUserId } from "@/lib/anonymous-user";
import { useActiveCurriculum } from "@/lib/active-curriculum";
import type { SessionHistoryDetail, SessionHistoryItem } from "@/lib/types";

import { HistoryList } from "./history-list";
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
  const { active } = useActiveCurriculum();
  const [items, setItems] = useState<SessionHistoryItem[] | null>(null);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [details, setDetails] = useState<Record<string, SessionHistoryDetail>>({});
  const [detailError, setDetailError] = useState("");
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [deletePromptId, setDeletePromptId] = useState<string | null>(null); const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadHistory = useCallback(async () => {
    const userId = getAnonymousUserId();
    const res = await fetch("/api/history/list", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, exam_id: active?.exam_id ?? "" }),
    });
    if (!res.ok) {
      setError("History is waiting for the agent service.");
      return;
    }
    const data = await res.json();
    setItems(data.sessions || []);
  }, [active?.exam_id]);

  useEffect(() => void loadHistory(), [loadHistory]);

  async function selectSession(id: string) {
    setSelectedId(id);
    setDetailError("");
    if (details[id]) return;
    setLoadingId(id);
    const userId = getAnonymousUserId();
    const res = await fetch("/api/history/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, exam_id: active?.exam_id ?? "", session_id: id }),
    });
    if (res.ok) {
      const data: SessionHistoryDetail = await res.json();
      setDetails((prev) => ({ ...prev, [id]: data }));
    } else {
      setDetailError("Couldn't load this session.");
    }
    setLoadingId(null);
  }

  const deleteSession = useCallback(async (id: string) => {
    const userId = getAnonymousUserId();
    setDeletingId(id);
    setDetailError("");
    const res = await fetch("/api/history/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, session_id: id }),
    });
    if (!res.ok) {
      setError("Couldn't delete this session.");
      setDeletingId(null);
      setDeletePromptId(null);
      return;
    }
    if (selectedId === id) {
      setSelectedId(null);
      setDetailError("");
    }
    setDetails((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
    setDeletePromptId(null);
    setDeletingId(null);
    await loadHistory();
  }, [loadHistory, selectedId]);

  const selectedItem = items?.find((item) => item.id === selectedId) || null; const selectedDetail = selectedId ? details[selectedId] : null;

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
              <HistoryList
                items={items}
                selectedId={selectedId}
                deletePromptId={deletePromptId}
                deletingId={deletingId}
                onSelect={selectSession}
                onDeletePrompt={setDeletePromptId}
                onDeleteCancel={() => setDeletePromptId(null)}
                onDeleteConfirm={(sessionId) => void deleteSession(sessionId)}
              />
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
              ) : loadingId === selectedId ? (
                <p className="text-sm text-zinc-500 dark:text-zinc-400">Loading exchanges...</p>
              ) : detailError ? (
                <p className="text-sm text-amber-700 dark:text-amber-200">{detailError}</p>
              ) : !selectedDetail ? null : (
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
