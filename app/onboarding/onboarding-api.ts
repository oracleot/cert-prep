import type { LearningStyle } from "@/lib/types";

const JSON_HEADERS = { "Content-Type": "application/json" };

export function startOnboardingRequest(input: {
  user_id: string;
  exam_name: string;
  learning_style: LearningStyle;
}) {
  return fetch("/api/onboarding/start", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(input),
  });
}

export function onboardingStateRequest(userId: string) {
  return fetch("/api/onboarding/state", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ user_id: userId }),
  });
}

export function dashboardSummaryRequest(userId: string) {
  return fetch("/api/dashboard/summary", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ user_id: userId }),
  });
}

export function supportedExamsRequest() {
  return fetch("/api/exams");
}
