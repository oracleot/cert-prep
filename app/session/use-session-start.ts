"use client";
// Phase 11 — start / restore / next lifecycle hook for the session page.
//
// Extracted from use-session.ts so the main hook stays under the 200-line
// hard rule. The returned handlers share state with use-session via the
// provided setters; refs are passed through to keep request-id tracking
// consistent across handlers.

import { useCallback, type Dispatch, type MutableRefObject, type SetStateAction } from "react";
import { loadSettings } from "@/lib/settings";
import { nextSessionRequest, restoreSessionRequest, startSessionRequest } from "./session-api";
import { type RestoredSession } from "./session-persistence";
import { bindThreadToActiveCurriculum, clearActiveThreadId } from "./session-scope";
import type { Challenge, Citation, EvaluationResult, SageFeedback, SessionResult } from "@/lib/types";

// Phase 11 — `setPhase` accepts the full SessionPhase string union. We type
// it as a generic string setter here; use-session.ts passes the narrower
// SessionPhase Dispatch which is structurally assignable.
type Setters = {
  setPhase: Dispatch<SetStateAction<string>>;
  setChallenge: Dispatch<SetStateAction<Challenge | null>>;
  setAnswer: Dispatch<SetStateAction<string>>;
  setEvaluation: Dispatch<SetStateAction<EvaluationResult | null>>;
  setSageText: Dispatch<SetStateAction<string>>;
  setSageCitations: Dispatch<SetStateAction<Citation[]>>;
  setSageFeedback: Dispatch<SetStateAction<SageFeedback | null>>;
  setResults: Dispatch<SetStateAction<SessionResult[]>>;
  setErrorMsg: Dispatch<SetStateAction<string>>;
  setThreadId: Dispatch<SetStateAction<string | null>>;
  setCycle: Dispatch<SetStateAction<number>>;
  setMaxCycles: Dispatch<SetStateAction<number>>;
};

export type SessionStartDeps = Setters & {
  activeRequestRef: MutableRefObject<number>;
  lastActionRef: MutableRefObject<"start" | "resume" | "submit" | "next">;
  threadId: string | null;
  applySnapshot: (snapshot: RestoredSession) => void;
  focusDomain: string;
  examId: string | null;
  startOverrides: { mode?: "new" | "review"; conceptId?: string };
  onFocusDomainConsumed?: () => void;
};

export function useSessionStart(deps: SessionStartDeps) {
  const {
    activeRequestRef, lastActionRef, setPhase, setChallenge, setAnswer, setEvaluation,
    setSageText, setSageCitations, setSageFeedback, setResults, setErrorMsg, setThreadId,
    setCycle, setMaxCycles, threadId, applySnapshot, focusDomain, examId, startOverrides,
    onFocusDomainConsumed,
  } = deps;

  const startSession = useCallback(async (showLoading = true) => {
    const requestId = ++activeRequestRef.current;
    lastActionRef.current = "start";
    if (showLoading) setPhase("loading_challenge");
    setChallenge(null); setAnswer("");
    setEvaluation(null); setSageText(""); setSageCitations([]); setSageFeedback(null);
    const res = await startSessionRequest({
      focusDomain,
      examId,
      mode: startOverrides.mode ?? "new",
      conceptId: startOverrides.conceptId ?? "",
    });
    if (requestId !== activeRequestRef.current) return;
    if (!res.ok) {
      setErrorMsg("Rex couldn't generate a challenge. Try again.");
      setPhase("error");
      return;
    }
    const data = await res.json();
    if (requestId !== activeRequestRef.current) return;
    bindThreadToActiveCurriculum(data.thread_id);
    setThreadId(data.thread_id);
    setCycle(1);
    setMaxCycles(data.max_cycles ?? loadSettings().sessionCycles);
    setResults([]);
    setChallenge(data.challenge);
    setPhase("ready");
    onFocusDomainConsumed?.();
  }, [activeRequestRef, lastActionRef, setPhase, setChallenge, setAnswer, setEvaluation, setSageText, setSageCitations, setSageFeedback, setResults, setErrorMsg, setThreadId, setCycle, setMaxCycles, focusDomain, examId, startOverrides.mode, startOverrides.conceptId, onFocusDomainConsumed]); // activeRequestRef is a stable ref, intentionally included for eslint

  const restoreSession = useCallback(async (sessionThreadId: string, showLoading = true): Promise<RestoredSession["phase"] | null | undefined> => {
    const requestId = ++activeRequestRef.current;
    lastActionRef.current = "resume";
    if (showLoading) setPhase("loading_challenge");
    const res = await restoreSessionRequest(sessionThreadId);
    if (requestId !== activeRequestRef.current) return undefined;
    if (res.status === 404) {
      clearActiveThreadId();
      setThreadId(null);
      return null;
    }
    if (!res.ok) {
      setErrorMsg("We couldn't restore your session. Retry in a moment.");
      setPhase("error");
      return null;
    }
    const data = (await res.json()) as RestoredSession;
    if (requestId !== activeRequestRef.current) return undefined;
    applySnapshot(data);
    return data.phase;
  }, [activeRequestRef, lastActionRef, setPhase, setErrorMsg, setThreadId, applySnapshot]); // activeRequestRef is a stable ref, intentionally included for eslint

  const loadNextChallenge = useCallback(async () => {
    if (!threadId) return;
    lastActionRef.current = "next";
    setPhase("loading_rechallenge");
    setChallenge(null); setAnswer("");
    setEvaluation(null); setSageText(""); setSageCitations([]); setSageFeedback(null);
    const res = await nextSessionRequest(threadId);
    if (!res.ok) {
      setErrorMsg("Rex couldn't generate a rechallenge. Try again.");
      setPhase("error");
      return;
    }
    const data = await res.json();
    setCycle(data.cycle);
    setChallenge(data.challenge);
    setPhase("ready");
  }, [lastActionRef, threadId, setPhase, setChallenge, setAnswer, setEvaluation, setSageText, setSageCitations, setSageFeedback, setErrorMsg, setCycle]);

  return { startSession, restoreSession, loadNextChallenge };
}