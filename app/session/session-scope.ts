// Curriculum ↔ session thread orchestration. Isolated from use-session.ts so
// the orchestrator stays focused on the Rex/Sage 2-cycle state machine and
// resume/clear policy lives in one place.

import { loadActiveCurriculum, useActiveCurriculum } from "@/lib/active-curriculum";
import {
  clearThreadIdForCurriculum,
  loadThreadIdForCurriculum,
  saveThreadMapEntry,
} from "./session-persistence";

/**
 * Returns the resumable thread_id for the active curriculum, or null when no
 * active curriculum is set (e.g. pre-onboarding) or no thread has been bound
 * to that curriculum yet. Re-runs on active-curriculum change so swapping
 * curricula in Settings immediately exposes the new curriculum's thread.
 *
 * Prior entries under the old curriculum_id are NOT touched.
 */
export function useResumableThreadId(): string | null {
  const { active } = useActiveCurriculum();
  if (!active) return null;
  return loadThreadIdForCurriculum(active.curriculum_id);
}

/**
 * Returns the exam_id of the active curriculum, or null. Used to thread the
 * exam_id through `/session/start` and `/session/state` so the LangGraph
 * service can attribute the session to the right exam.
 */
export function useActiveExamId(): string | null {
  const { active } = useActiveCurriculum();
  return active?.exam_id ?? null;
}

/**
 * Persist a newly-started thread_id under the active curriculum. Read at
 * call time (not at hook-render time) so a curriculum switch that lands
 * during a callback is still honored. No-op without an active curriculum.
 * Uses the non-hook `loadActiveCurriculum` so it stays safe to call from
 * useCallback bodies and event handlers.
 */
export function bindThreadToActiveCurriculum(threadId: string): void {
  const active = loadActiveCurriculum();
  if (!active || !threadId) return;
  saveThreadMapEntry(active.curriculum_id, threadId);
}

/**
 * Clear the resumable thread entry for the active curriculum. Used on
 * 404 during resume, on `restart`, and on `abandonSession`. Other
 * curricula's entries are preserved. Non-hook so it can run from any
 * call site.
 */
export function clearActiveThreadId(): void {
  const active = loadActiveCurriculum();
  if (!active) return;
  clearThreadIdForCurriculum(active.curriculum_id);
}
