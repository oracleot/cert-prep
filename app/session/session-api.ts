import { getAnonymousUserId } from "@/lib/anonymous-user";
import { getBrowserTimezone } from "@/lib/browser-timezone";
import { loadSettings, sessionSettingsPayload } from "@/lib/settings";
import type { AnswerIntent, SageFeedbackType } from "@/lib/types";

const JSON_HEADERS = { "Content-Type": "application/json" };

export function startSessionRequest(focusDomain = "") {
  return fetch("/api/session/start", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({
      user_id: getAnonymousUserId(),
      timezone: getBrowserTimezone(),
      ...sessionSettingsPayload(loadSettings()),
      ...(focusDomain ? { focus_domain: focusDomain } : {}),
    }),
  });
}

export function restoreSessionRequest(threadId: string) {
  return fetch("/api/session/state", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ thread_id: threadId }),
  });
}

export function nextSessionRequest(threadId: string) {
  return fetch("/api/session/next", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ thread_id: threadId, ...sessionSettingsPayload(loadSettings()) }),
  });
}

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

export function submitSageFeedbackRequest(threadId: string, cycle: number, feedbackType: SageFeedbackType, comment: string) {
  return fetch("/api/session/feedback", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ thread_id: threadId, cycle, feedback_type: feedbackType, comment }),
  });
}
