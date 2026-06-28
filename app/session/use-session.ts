"use client";
import { useCallback, useRef, useState } from "react";
import type { AnswerIntent, Challenge, Citation, EvaluationResult, SageFeedback, SageFeedbackType, SessionResult } from "@/lib/types";
import { DEFAULT_SETTINGS, loadSettings } from "@/lib/settings";
import { nextSessionRequest, restoreSessionRequest, startSessionRequest, submitSageFeedbackRequest, submitSessionRequest } from "./session-api";
import { type RestoredSession } from "./session-persistence";
import { readSessionStream } from "./session-stream";
import { useRexRecord } from "./use-rex-record";
import { answerIntentFor, answerTextFor } from "./answer-intent";
import { bindThreadToActiveCurriculum, clearActiveThreadId, useActiveExamId, useResumableThreadId } from "./session-scope";
import { useSessionLifecycle } from "./use-session-lifecycle";
export type SessionPhase = "loading_challenge" | "ready" | "evaluating" | "streaming_sage" | "sage_done" | "loading_rechallenge" | "summary" | "error";
type SessionAction = "start" | "resume" | "submit" | "next";
export function useSession(
  focusDomain = "",
  onFocusDomainConsumed?: () => void,
  startOverrides: { mode?: "new" | "review"; conceptId?: string } = {},
) {
  const [phase, setPhase] = useState<SessionPhase>("loading_challenge");
  const [cycle, setCycle] = useState(1);
  const [maxCycles, setMaxCycles] = useState(DEFAULT_SETTINGS.sessionCycles);
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [answer, setAnswer] = useState("");
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [sageText, setSageText] = useState("");
  const [sageCitations, setSageCitations] = useState<Citation[]>([]);
  const [sageFeedback, setSageFeedback] = useState<SageFeedback | null>(null);
  const [results, setResults] = useState<SessionResult[]>([]);
  const [errorMsg, setErrorMsg] = useState("");
  const [threadId, setThreadId] = useState<string | null>(null);
  const lastActionRef = useRef<SessionAction>("start");
  const activeRequestRef = useRef(0);
  const { rexRecord, refreshRexRecord } = useRexRecord();
  const resumableThreadId = useResumableThreadId();
  const examId = useActiveExamId();
  const applySnapshot = useCallback((snapshot: RestoredSession) => {
    setThreadId(snapshot.thread_id);
    bindThreadToActiveCurriculum(snapshot.thread_id);
    setCycle(snapshot.cycle);
    setMaxCycles(snapshot.max_cycles);
    setChallenge(snapshot.challenge); setAnswer(snapshot.user_answer);
    setEvaluation(snapshot.evaluation); setSageText(snapshot.sage_text);
    setSageCitations(snapshot.sage_citations ?? []); setSageFeedback(snapshot.sage_feedback ?? null);
    setResults(snapshot.results);
    setErrorMsg("");
    setPhase(snapshot.phase);
  }, []);
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
  }, [focusDomain, examId, onFocusDomainConsumed, startOverrides.mode, startOverrides.conceptId]);
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
    },
    [applySnapshot],
  );
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
  }, [threadId]);
  const submitAnswer = useCallback(async (intent: AnswerIntent = "attempt") => {
    const nextIntent = answerIntentFor(answer, intent);
    const nextAnswer = answerTextFor(answer, nextIntent);
    if (!challenge || !nextAnswer.trim() || !threadId) return;
    lastActionRef.current = "submit";
    setPhase("evaluating");
    setAnswer(nextAnswer);
    const res = await submitSessionRequest(threadId, nextAnswer, nextIntent);
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
        nextEvaluation.answer_intent ??= nextIntent;
        currentEvaluation = nextEvaluation;
        setEvaluation(nextEvaluation);
        setPhase("streaming_sage");
      },
      onToken: (token) => { accumulatedSageText += token; setSageText(accumulatedSageText); },
      onCitations: setSageCitations,
      onDone: () => {
        if (currentEvaluation) setResults((prev) => [...prev, { cycle, topic: challenge.topic, outcome: currentEvaluation!.outcome, answer_intent: nextIntent }]);
        void refreshRexRecord();
        setPhase("sage_done");
      },
      onError: (message) => { setErrorMsg(message); setPhase("error"); },
    });
  }, [challenge, answer, cycle, refreshRexRecord, threadId]);
  const nextChallenge = useCallback(async () => {
    if (!challenge) return;
    if (cycle >= maxCycles) {
      setPhase("summary");
      return;
    }
    await loadNextChallenge();
  }, [challenge, cycle, loadNextChallenge, maxCycles]);
  const submitSageFeedback = useCallback(async (feedbackType: SageFeedbackType, comment: string) => {
    if (!threadId) throw new Error("Session is unavailable.");
    const res = await submitSageFeedbackRequest(threadId, cycle, feedbackType, comment);
    if (!res.ok) throw new Error("Feedback failed to save. Try again.");
    const data = await res.json();
    const feedback = data.feedback as SageFeedback;
    setSageFeedback(feedback);
    setResults((prev) => prev.map((item) => item.cycle === cycle ? { ...item, feedback, review_status: feedback.review_status } : item));
    if (feedback.excludes_metrics) void refreshRexRecord();
  }, [cycle, refreshRexRecord, threadId]);
  const retry = useCallback(async () => {
    const action = lastActionRef.current;
    if (action === "start" || !threadId) {
      await startSession();
      return;
    }
    const restoredPhase = await restoreSession(threadId);
    if (restoredPhase === undefined) return;
    if (restoredPhase === null) {
      await startSession();
      return;
    }
    if (action === "submit" && restoredPhase === "ready" && answer.trim()) await submitAnswer();
    if (action === "next" && restoredPhase === "sage_done") await loadNextChallenge();
  }, [answer, loadNextChallenge, restoreSession, startSession, submitAnswer, threadId]);
  const restart = useCallback(() => {
    clearActiveThreadId();
    setCycle(1); setResults([]);
    setErrorMsg(""); setThreadId(null);
    void startSession();
  }, [startSession]);
  const clearThread = () => setThreadId(null);
  const bumpRequest = () => { activeRequestRef.current += 1; };
  const { abandonSession } = useSessionLifecycle({ startSession, restoreSession, onFocusDomainConsumed, resumableThreadId, startOverrides, clearThread, bumpRequest });
  return { phase, cycle, maxCycles, domain: challenge?.domain ?? "Exam", challenge, answer, setAnswer, evaluation, sageText, sageCitations, sageFeedback, results, rexRecord, errorMsg, submitAnswer, submitSageFeedback, nextChallenge, retry, restart, abandonSession };
}
