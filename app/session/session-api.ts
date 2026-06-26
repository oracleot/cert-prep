import { getAnonymousUserId } from "@/lib/anonymous-user";
import { getBrowserTimezone } from "@/lib/browser-timezone";
import { loadSettings, sessionSettingsPayload } from "@/lib/settings";
import type { AnswerIntent, SageFeedbackType } from "@/lib/types";

const JSON_HEADERS = { "Content-Type": "application/json" };

/**
 * POST /api/session/start
 *
 * Kicks off a fresh LangGraph session for the active curriculum. The
 * `exam_id` is required so the agent service can attribute progress to the
 * right exam. The response payload includes the server-generated
 * `thread_id` and the active `curriculum_id`; the client must bind the
 * thread to the active curriculum for later resume.
 *
 * `thread_id` is intentionally not sent here — the server generates one.
 * Resumes go through `restoreSessionRequest` instead.
 */
export function startSessionRequest(focusDomain = "", examId: string | null = null) {
  return fetch("/api/session/start", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      user_id: getAnonymousUserId(),
      timezone: getBrowserTimezone(),
      ...(examId ? { exam_id: examId } : {}),
      ...sessionSettingsPayload(loadSettings()),
      ...(focusDomain ? { focus_domain: focusDomain } : {}),
    }),
  });
}

/**
 * POST /api/session/state
 *
 * Rehydrates a previously-started session by its `thread_id`. Returns the
 * full RestoredSession snapshot (challenge, evaluation, sage text, results)
 * that the client applies on mount when the active curriculum has a bound
 * thread. 404 means the server has no record of the thread; the client
 * treats that as "thread expired — start a fresh session".
 */
export function restoreSessionRequest(threadId: string) {
  return fetch("/api/session/state", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ thread_id: threadId }),
  });
}

/**
 * POST /api/session/next
 *
 * Asks Rex to generate the next challenge in the existing thread. Called
 * after the user finishes a Sage explanation and taps "Next".
 */
export function nextSessionRequest(threadId: string) {
  return fetch("/api/session/next", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ thread_id: threadId, ...sessionSettingsPayload(loadSettings()) }),
  });
}

/**
 * POST /api/session/submit
 *
 * Submits the user's answer for the current challenge. Returns an SSE
 * stream (evaluation → citations → token* → done) consumed by
 * `readSessionStream`.
 */
export function submitSessionRequest(threadId: string, userAnswer: string, answerIntent: AnswerIntent) {
  return fetch("/api/session/submit", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      thread_id: threadId,
      user_answer: userAnswer,
      answer_intent: answerIntent,
      ...sessionSettingsPayload(loadSettings()),
    }),
  });
}

/**
 * POST /api/session/feedback
 *
 * Records the user's feedback on Sage's explanation (factual_error,
 * bad_source, confusing_explanation). Affects the exchange's
 * `review_status` and may exclude it from Rex's win/loss metrics.
 */
export function submitSageFeedbackRequest(threadId: string, cycle: number, feedbackType: SageFeedbackType, comment: string) {
  return fetch("/api/session/feedback", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ thread_id: threadId, cycle, feedback_type: feedbackType, comment }),
  });
}
