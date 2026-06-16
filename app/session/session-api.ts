import { getAnonymousUserId } from "@/lib/anonymous-user";

const JSON_HEADERS = { "Content-Type": "application/json" };

export function startSessionRequest() {
  return fetch("/api/session/start", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ user_id: getAnonymousUserId() }),
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
    body: JSON.stringify({ thread_id: threadId }),
  });
}

export function submitSessionRequest(threadId: string, userAnswer: string) {
  return fetch("/api/session/submit", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ thread_id: threadId, user_answer: userAnswer }),
  });
}
