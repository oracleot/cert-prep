"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { useActiveCurriculum } from "@/lib/active-curriculum";
import { getAnonymousUserId } from "@/lib/anonymous-user";
import { getExamName } from "@/lib/exam-names";

type Curriculum = {
  curriculum_id: string;
  exam_id: string;
  exam_name: string;
  learning_style: string;
  active: boolean;
  created_at: string;
};

type ListResponse = { curricula: Curriculum[] };
type SwitchResponse =
  | { status: "ready"; exam_id: string; exam_name: string; curriculum_id: string }
  | { status: "needs_onboarding"; exam_id: string; exam_name: string; redirect_to: string };

export function CurriculumSwitcher() {
  const { active, setActive } = useActiveCurriculum();
  const [curricula, setCurricula] = useState<Curriculum[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingExamId, setPendingExamId] = useState<string | null>(null);
  const [switchRedirect, setSwitchRedirect] = useState<{ exam_id: string; exam_name: string; href: string } | null>(null);
  const [confirmation, setConfirmation] = useState<string | null>(null);

  const loadList = useCallback(() => {
    return fetch("/api/settings/curricula", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: getAnonymousUserId() }),
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<ListResponse>;
      })
      .then((data) => {
        setCurricula(data.curricula ?? []);
        setError(null);
      })
      .catch(() => {
        setError("Could not load curricula. Try again.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const refresh = useCallback(() => {
    setLoading(true);
    setError(null);
    void loadList();
  }, [loadList]);

  useEffect(() => {
    void loadList();
  }, [loadList]);

  const onSwitch = useCallback(
    async (examId: string) => {
      setPendingExamId(examId);
      setSwitchRedirect(null);
      setError(null);
      try {
        const res = await fetch("/api/settings/curriculum-switch", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: getAnonymousUserId(), exam_id: examId }),
        });
        if (!res.ok) {
          setError("Switch failed. Try again.");
          return;
        }
        const data = (await res.json()) as SwitchResponse;
        if (data.status === "needs_onboarding") {
          setSwitchRedirect({ exam_id: data.exam_id, exam_name: data.exam_name, href: data.redirect_to });
          return;
        }
        setActive({
          exam_id: data.exam_id,
          exam_name: data.exam_name,
          curriculum_id: data.curriculum_id,
          saved_at: new Date().toISOString(),
        });
        setConfirmation(`Now using ${data.exam_name}.`);
        await loadList();
      } catch {
        setError("Switch failed. Try again.");
      } finally {
        setPendingExamId(null);
      }
    },
    [loadList, setActive],
  );

  const activeId = active?.curriculum_id ?? null;

  return (
    <div className="rounded-[2rem] border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950 lg:col-span-2">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-xl font-black">Curriculum</h2>
          <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
            Choose which exam is active across Dashboard, Session, Progress, and History.
          </p>
        </div>
        <Button variant="outline" onClick={refresh} disabled={loading}>Refresh</Button>
      </div>

      {loading && curricula.length === 0 ? (
        <p className="mt-5 text-sm text-zinc-500 dark:text-zinc-400">Loading curricula…</p>
      ) : error ? (
        <div className="mt-5 flex flex-wrap items-center gap-3">
          <p className="text-sm text-rose-700 dark:text-rose-300">{error}</p>
          <Button variant="outline" onClick={refresh}>Retry</Button>
        </div>
      ) : curricula.length === 0 ? (
        <div className="mt-5">
          <p className="text-sm text-zinc-600 dark:text-zinc-300">
            No curricula built yet. Start with DVA-C02 to activate your account.
          </p>
          <Button asChild className="mt-4 bg-amber-300 text-zinc-950 hover:bg-amber-200">
            <a href="/onboarding?exam=dva-c02&source=settings">Build DVA-C02 curriculum</a>
          </Button>
        </div>
      ) : (
        <ul className="mt-5 grid gap-3">
          {curricula.map((c) => {
            const isActive = c.curriculum_id === activeId || c.active;
            const isPending = pendingExamId === c.exam_id;
            return (
              <li
                key={c.curriculum_id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-900"
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-black text-zinc-950 dark:text-zinc-50">{c.exam_name || getExamName(c.exam_id)}</span>
                    {isActive ? (
                      <span className="rounded-full bg-amber-300 px-2 py-0.5 text-[10px] font-black uppercase tracking-widest text-zinc-950">Active</span>
                    ) : null}
                  </div>
                  <p className="mt-1 text-xs font-semibold uppercase tracking-widest text-zinc-500 dark:text-zinc-400">
                    {c.exam_id} · {c.learning_style}
                  </p>
                </div>
                {switchRedirect && switchRedirect.exam_id === c.exam_id ? (
                  <Button asChild className="bg-amber-300 text-zinc-950 hover:bg-amber-200">
                    <a href={switchRedirect.href}>Build {switchRedirect.exam_name || getExamName(c.exam_id)} curriculum</a>
                  </Button>
                ) : isActive ? (
                  <Button variant="outline" disabled>Current</Button>
                ) : (
                  <Button onClick={() => onSwitch(c.exam_id)} disabled={isPending} className="bg-amber-300 text-zinc-950 hover:bg-amber-200">
                    {isPending ? "Switching…" : `Switch to ${c.exam_name || getExamName(c.exam_id)}`}
                  </Button>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {confirmation ? (
        <p className="mt-4 text-sm font-bold text-emerald-700 dark:text-emerald-300" role="status">{confirmation}</p>
      ) : null}
    </div>
  );
}
