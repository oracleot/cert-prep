import type { AnswerIntent, Challenge, Citation, EvaluationResult, SageFeedback, SessionResult } from "@/lib/types";

const SESSION_THREAD_KEY = "gauntlet.session.thread-id";

export type RestoredSession = {
  thread_id: string;
  phase: "ready" | "sage_done" | "summary";
  cycle: number;
  max_cycles: number;
  challenge: Challenge | null;
  user_answer: string;
  answer_intent?: AnswerIntent;
  evaluation: EvaluationResult | null;
  sage_text: string;
  sage_citations: Citation[];
  sage_feedback?: SageFeedback | null;
  results: SessionResult[];
};

export function loadThreadId(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(SESSION_THREAD_KEY);
}

export function saveThreadId(threadId: string) {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(SESSION_THREAD_KEY, threadId);
}

export function clearThreadId() {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(SESSION_THREAD_KEY);
}
