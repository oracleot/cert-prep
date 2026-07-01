"use client";
// Phase 11 — start / restore / next lifecycle hook for the session page.
//
// Extracted from use-session.ts so the main hook stays under the 200-line
// hard rule. The returned handlers share state with use-session via the
// provided setters.

import { useCallback } from "react";
import { DEFAULT_SETTINGS, loadSettings } from "@/lib/settings";
import { nextSessionRequest, restoreSessionRequest, startSessionRequest } from "./session-api";
import { type RestoredSession } from "./session-persistence";
import { bindThreadToActiveCurriculum, clearActiveThreadId } from "./session-scope";
import type { Challenge, Citation, EvaluationResult, SageFeedback, SessionResult } from "@/lib/types";

export type SessionStartDeps = {
  activeRequestRef: React.MutableRefObject<number>;
  lastActionRef: React.MutableRefObject<"start" | "resume" | "submit" | "next">;
  setPhase: (p: "loading_challenge" | "ready" | "loading_rechallenge" | "error") => void;
  setChallenge: (c: Challenge | null) => void;
  setAnswer: (s: string) => void;
  setEvaluation: (e: EvaluationResult | null) => void;
  setSageText: (s: string) => void;
  setSageCitations: (c: Citation[]) => void;
  setSageFeedback: (f: SageFeedback | null) => void;
  setResults: (r: SessionResult[]) => void;
  setErrorMsg: (s: string) => void;
  setThreadId: (s: string | null) => void;
  setCycle: (n: number) => void;
  setMaxCycles: (n: number) => void;
  threadId: string | null;
  applySnapshot: (snapshot: RestoredSession) => void;
  focusDomain: string;
  examId: string | null;
  startOverrides: { mode?: "new" | "review"; conceptId?: string };
  onFocusDomainConsumed?: () => void;
};

export function useSessionStart(deps: SessionStartDeps) {
  const { focusDomain, examId, startOverrides, onFocusDomainConsumed } = deps;
  const startSession = useCallback(async (showLoading = true) => {
    const requestId = ++deps.activeRequestRef.current;
    deps.lastActionRef.current = "start";
    if (showLoading) deps.setPhase("loading_challenge");
    deps.setChallenge(null); deps.setAnswer("");
    deps.setEvaluation(null); deps.setSageText(""); deps.setSageCitations([]); deps.setSageFeedback(null);
    const res = await startSessionRequest({
      focusDomain,
      examId,
      mode: startOverrides.mode ?? "new",
      conceptId: startOverrides.conceptId ?? "",
    });
    if (requestId !== deps.activeRequestRef.current) return;
    if (!res.ok) {
      deps.setErrorMsg("Rex couldn't generate a challenge. Try again.");
      deps.setPhase("error");
      return;
    }
    const data = await res.json();
    if (requestId !== deps.activeRequestRef.current) return;
    bindThreadToActiveCurriculum(data.thread_id);
    deps.setThreadId(data.thread_id);
    deps.setCycle(1);
    deps.setMaxCycles(data.max_cycles ?? loadSettings().sessionCycles);
    deps.setResults([]);
    deps.setChallenge(data.challenge);
    deps.setPhase("ready");
    onFocusDomainConsumed?.();
  }, [deps, focusDomain, examId, onFocusDomainConsumed, startOverrides.mode, startOverrides.conceptId]);

  const restoreSession = useCallback(async (sessionThreadId: string, showLoading = true): Promise<RestoredSession["phase"] | null | undefined> => {
    const requestId = ++deps.activeRequestRef.current;
    deps.lastActionRef.current = "resume";
    if (showLoading) deps.setPhase("loading_challenge");
    const res = await restoreSessionRequest(sessionThreadId);
    if (requestId !== deps.activeRequestRef.current) return undefined;
    if (res.status === 404) {
      clearActiveThreadId();
      deps.setThreadId(null);
      return null;
    }
    if (!res.ok) {
      deps.setErrorMsg("We couldn't restore your session. Retry in a moment.");
      deps.setPhase("error");
      return null;
    }
    const data = (await res.json()) as RestoredSession;
    if (requestId !== deps.activeRequestRef.current) return undefined;
    deps.applySnapshot(data);
    return data.phase;
  }, [deps]);

  const loadNextChallenge = useCallback(async () => {
    if (!deps.threadId) return;
    deps.lastActionRef.current = "next";
    deps.setPhase("loading_rechallenge");
    deps.setChallenge(null); deps.setAnswer("");
    deps.setEvaluation(null); deps.setSageText(""); deps.setSageCitations([]); deps.setSageFeedback(null);
    const res = await nextSessionRequest(deps.threadId);
    if (!res.ok) {
      deps.setErrorMsg("Rex couldn't generate a rechallenge. Try again.");
      deps.setPhase("error");
      return;
    }
    const data = await res.json();
    deps.setCycle(data.cycle);
    deps.setChallenge(data.challenge);
    deps.setPhase("ready");
  }, [deps]);

  return { startSession, restoreSession, loadNextChallenge };
}