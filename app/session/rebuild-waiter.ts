// Polls GET /api/settings/curricula after a learning-style rebuild until a
// new active curriculum_id appears for the target exam. Used by the
// Settings page to promote the rebuild result to active without forcing
// the user to navigate into /onboarding.

import { getAnonymousUserId } from "@/lib/anonymous-user";

export type RebuiltCurriculum = {
  curriculum_id: string;
  exam_id: string;
  exam_name: string;
  active: boolean;
};

type ListResponse = { curricula: RebuiltCurriculum[] };
type WaitOpts = {
  userId: string;
  examId: string;
  prevCurriculumId: string | undefined;
  intervalMs?: number;
  timeoutMs?: number;
};

const DEFAULT_INTERVAL_MS = 1500;
const DEFAULT_TIMEOUT_MS = 30_000;

async function fetchActiveForExam(userId: string, examId: string): Promise<RebuiltCurriculum | null> {
  try {
    const res = await fetch("/api/settings/curricula", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId }),
    });
    if (!res.ok) return null;
    const data = (await res.json()) as ListResponse;
    return data.curricula.find((c) => c.exam_id === examId && c.active) ?? null;
  } catch {
    return null;
  }
}

/**
 * Returns the new active curriculum for `examId` once a rebuild produces a
 * different `curriculum_id` than `prevCurriculumId`, or `null` on timeout.
 * No-ops (returns null) when `userId` or `examId` is empty.
 */
export async function waitForRebuild(opts: WaitOpts): Promise<RebuiltCurriculum | null> {
  const { userId, examId, prevCurriculumId } = opts;
  const intervalMs = opts.intervalMs ?? DEFAULT_INTERVAL_MS;
  const timeoutMs = opts.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  if (!userId || !examId) return null;
  const effectiveUserId = userId || getAnonymousUserId();

  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const found = await fetchActiveForExam(effectiveUserId, examId);
    if (found && found.curriculum_id !== prevCurriculumId) return found;
    await new Promise((resolve) => window.setTimeout(resolve, intervalMs));
  }
  return null;
}