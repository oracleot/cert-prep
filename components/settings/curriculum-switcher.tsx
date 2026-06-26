"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { useActiveCurriculum } from "@/lib/active-curriculum";
import { getAnonymousUserId } from "@/lib/anonymous-user";
import { EXAM_NAMES, getExamName } from "@/lib/exam-names";

// All three V1-bundled exams render as switch targets regardless of DB state.
// The API only decides "Active" chip vs "Switch to X" vs "Build X curriculum".
const BUNDLED_EXAMS = Object.keys(EXAM_NAMES) as Array<keyof typeof EXAM_NAMES>;

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
  const initialLoading = loading && curricula.length === 0;

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

      {initialLoading ? (
        <p className="mt-5 text-sm text-zinc-500 dark:text-zinc-400">Loading curricula…</p>
      ) : error && curricula.length === 0 ? (
        <div className="mt-5 flex flex-wrap items-center gap-3">
          <p className="text-sm text-rose-700 dark:text-rose-300">{error}</p>
          <Button variant="outline" onClick={refresh}>Retry</Button>
        </div>
      ) : (
        <ul className="mt-5 grid gap-3">
          {BUNDLED_EXAMS.map((examId) => {
            const apiCurriculum = curricula.find((c) => c.exam_id === examId);
            const examName = getExamName(examId);
            const isActive = !!apiCurriculum && apiCurriculum.curriculum_id === activeId;
            const isLocallyActive = !apiCurriculum && active?.exam_id === examId;
            const showActiveChip = isActive || isLocallyActive;
            const isPending = pendingExamId === examId;
            const redirectHere =
              switchRedirect && switchRedirect.exam_id === examId ? switchRedirect : null;

            return (
              <li
                key={examId}
                className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-900"
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-black text-zinc-950 dark:text-zinc-50">{examName}</span>
                    {showActiveChip ? (
                      <span className="rounded-full bg-amber-300 px-2 py-0.5 text-[10px] font-black uppercase tracking-widest text-zinc-950">Active</span>
                    ) : null}
                  </div>
                  <p className="mt-1 text-xs font-semibold uppercase tracking-widest text-zinc-500 dark:text-zinc-400">
                    {examId}
                    {apiCurriculum ? ` · ${apiCurriculum.learning_style}` : " · not built"}
                  </p>
                </div>
                {redirectHere ? (
                  <Button asChild className="bg-amber-300 text-zinc-950 hover:bg-amber-200">
                    <a href={redirectHere.href}>Build {redirectHere.exam_name || examName} curriculum</a>
                  </Button>
                ) : showActiveChip ? (
                  <Button variant="outline" disabled>Current</Button>
                ) : apiCurriculum ? (
                  <Button onClick={() => onSwitch(examId)} disabled={isPending} className="bg-amber-300 text-zinc-950 hover:bg-amber-200">
                    {isPending ? "Switching…" : `Switch to ${examName}`}
                  </Button>
                ) : (
                  <Button asChild className="bg-amber-300 text-zinc-950 hover:bg-amber-200">
                    <a href={`/onboarding?exam=${examId}&source=settings`}>Build {examName} curriculum</a>
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
