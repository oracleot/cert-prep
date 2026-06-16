"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Challenge, Citation, EvaluationResult, SessionResult } from "@/lib/types";
import { nextSessionRequest, restoreSessionRequest, startSessionRequest, submitSessionRequest } from "./session-api";
import { clearThreadId, loadThreadId, type RestoredSession, saveThreadId } from "./session-persistence";
import { readSessionStream } from "./session-stream";

export type SessionPhase = "loading_challenge" | "ready" | "evaluating" | "streaming_sage" | "sage_done" | "loading_rechallenge" | "summary" | "error";
const DEFAULT_CYCLES = 2;
type SessionAction = "start" | "resume" | "submit" | "next";
export function useSession() {
  const [phase, setPhase] = useState<SessionPhase>("loading_challenge");
  const [cycle, setCycle] = useState(1);
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [answer, setAnswer] = useState("");
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [sageText, setSageText] = useState("");
  const [sageCitations, setSageCitations] = useState<Citation[]>([]);
  const [results, setResults] = useState<SessionResult[]>([]);
  const [errorMsg, setErrorMsg] = useState("");
  const [threadId, setThreadId] = useState<string | null>(null);
  const lastActionRef = useRef<SessionAction>("start");
  const applySnapshot = useCallback((snapshot: RestoredSession) => {
    setThreadId(snapshot.thread_id);
    saveThreadId(snapshot.thread_id);
    setCycle(snapshot.cycle);
    setChallenge(snapshot.challenge);
    setAnswer(snapshot.user_answer);
    setEvaluation(snapshot.evaluation);
    setSageText(snapshot.sage_text);
    setSageCitations(snapshot.sage_citations ?? []);
    setResults(snapshot.results);
    setErrorMsg("");
    setPhase(snapshot.phase);
  }, []);
  const startSession = useCallback(async (showLoading = true) => {
    lastActionRef.current = "start";
    if (showLoading) setPhase("loading_challenge");
    setChallenge(null);
    setAnswer("");
    setEvaluation(null);
    setSageText("");
    setSageCitations([]);
    const res = await startSessionRequest();
    if (!res.ok) {
      setErrorMsg("Rex couldn't generate a challenge. Try again.");
      setPhase("error");
      return;
    }
    const data = await res.json();
    saveThreadId(data.thread_id);
    setThreadId(data.thread_id);
    setCycle(1);
    setResults([]);
    setChallenge(data.challenge);
    setPhase("ready");
  }, []);
  const restoreSession = useCallback(async (sessionThreadId: string, showLoading = true): Promise<RestoredSession["phase"] | null> => {
      lastActionRef.current = "resume";
      if (showLoading) setPhase("loading_challenge");
      const res = await restoreSessionRequest(sessionThreadId);
      if (res.status === 404) {
        clearThreadId();
        setThreadId(null);
        return null;
      }
      if (!res.ok) {
        setErrorMsg("We couldn't restore your session. Retry in a moment.");
        setPhase("error");
        return null;
      }
      const data = (await res.json()) as RestoredSession;
      applySnapshot(data);
      return data.phase;
    },
    [applySnapshot],
  );
  const loadNextChallenge = useCallback(async () => {
    if (!threadId) return;
    lastActionRef.current = "next";
    setPhase("loading_rechallenge");
    setChallenge(null);
    setAnswer("");
    setEvaluation(null);
    setSageText("");
    setSageCitations([]);
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
  }, [threadId]);
  const submitAnswer = useCallback(async () => {
    if (!challenge || !answer.trim() || !threadId) return;
    lastActionRef.current = "submit";
    setPhase("evaluating");
    const res = await submitSessionRequest(threadId, answer);
    if (!res.ok || !res.body) {
      setErrorMsg("Evaluation failed. Try again.");
      setPhase("error");
      return;
    }

    let currentEvaluation: EvaluationResult | null = null;
    let accumulatedSageText = "";
    setSageCitations([]);
    await readSessionStream(res.body, {
      onEvaluation: (nextEvaluation) => {
        currentEvaluation = nextEvaluation;
        setEvaluation(nextEvaluation);
        setPhase("streaming_sage");
      },
      onToken: (token) => {
        accumulatedSageText += token;
        setSageText(accumulatedSageText);
      },
      onCitations: setSageCitations,
      onDone: () => {
        const completedEvaluation = currentEvaluation;
        if (completedEvaluation) {
          setResults((prev) => [...prev, { cycle, topic: challenge.topic, outcome: completedEvaluation.outcome }]);
        }
        setPhase("sage_done");
      },
      onError: (message) => {
        setErrorMsg(message);
        setPhase("error");
      },
    });
  }, [challenge, answer, cycle, threadId]);

  const nextChallenge = useCallback(async () => {
    if (!challenge) return;
    if (cycle >= DEFAULT_CYCLES) {
      setPhase("summary");
      return;
    }
    await loadNextChallenge();
  }, [challenge, cycle, loadNextChallenge]);

  const retry = useCallback(async () => {
    const action = lastActionRef.current;
    if (action === "start" || !threadId) {
      await startSession();
      return;
    }
    const restoredPhase = await restoreSession(threadId);
    if (!restoredPhase) {
      await startSession();
      return;
    }
    if (action === "submit" && restoredPhase === "ready" && answer.trim()) await submitAnswer();
    if (action === "next" && restoredPhase === "sage_done") await loadNextChallenge();
  }, [answer, loadNextChallenge, restoreSession, startSession, submitAnswer, threadId]);

  const restart = useCallback(() => {
    clearThreadId();
    setCycle(1);
    setResults([]);
    setErrorMsg("");
    setThreadId(null);
    void startSession();
  }, [startSession]);

  useEffect(() => {
    const savedThreadId = loadThreadId();
    queueMicrotask(() => {
      if (savedThreadId) {
        void restoreSession(savedThreadId, false).then((restoredPhase) => !restoredPhase && void startSession(false));
        return;
      }
      void startSession(false);
    });
  }, [restoreSession, startSession]);

  return {
    phase,
    cycle,
    maxCycles: DEFAULT_CYCLES,
    domain: challenge?.domain ?? "Exam",
    challenge,
    answer,
    setAnswer,
    evaluation,
    sageText,
    sageCitations,
    results,
    errorMsg,
    submitAnswer,
    nextChallenge,
    retry,
    restart,
  };
}
