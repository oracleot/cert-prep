// Per-curriculum session thread map. Resumability is scoped to the active
// curriculum so switching curricula preserves each one's LangGraph thread.
//
// Storage shape:
//   sessionStorage["gauntlet.session.thread-map.v1"]
//     -> { [curriculum_id: string]: thread_id }
//
// Same-tab subscribers can listen to the "gauntlet:thread-map-changed"
// CustomEvent for re-render hooks that don't go through localStorage's
// cross-tab `storage` event (which only fires for *other* tabs).

import { loadActiveCurriculum } from "@/lib/active-curriculum";
import type { AnswerIntent, Challenge, Citation, EvaluationResult, SageFeedback, SessionResult } from "@/lib/types";

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

export type ThreadMap = Record<string, string>;

const THREAD_MAP_KEY = "gauntlet.session.thread-map.v1";
const LEGACY_THREAD_KEY = "gauntlet.session.thread-id";
const MIGRATION_FLAG_KEY = "gauntlet.session.thread-map.v1.migrated";
const THREAD_MAP_EVENT = "gauntlet:thread-map-changed";

const isBrowser = typeof window !== "undefined";

function dispatchChange(curriculumId: string, threadId: string) {
  if (!isBrowser) return;
  window.dispatchEvent(new CustomEvent(THREAD_MAP_EVENT, { detail: { curriculumId, threadId } }));
}

/**
 * One-shot adoption of the pre-V1 single-key thread_id (which lived in
 * sessionStorage) under the active curriculum. Idempotent and gated by a
 * localStorage flag so the cost is a single key lookup after the first run.
 */
function migrateLegacyThreadId(): void {
  if (!isBrowser) return;
  if (window.localStorage.getItem(MIGRATION_FLAG_KEY) === "1") return;
  const legacy = window.sessionStorage.getItem(LEGACY_THREAD_KEY);
  if (!legacy) {
    window.localStorage.setItem(MIGRATION_FLAG_KEY, "1");
    return;
  }
  const active = loadActiveCurriculum();
  if (!active) return; // Wait for an active curriculum; subsequent reads will retry.
  const map = readRawMap();
  if (!map[active.curriculum_id]) {
    map[active.curriculum_id] = legacy;
    window.sessionStorage.setItem(THREAD_MAP_KEY, JSON.stringify(map));
    dispatchChange(active.curriculum_id, legacy);
  }
  window.sessionStorage.removeItem(LEGACY_THREAD_KEY);
  window.localStorage.setItem(MIGRATION_FLAG_KEY, "1");
}

function readRawMap(): ThreadMap {
  if (!isBrowser) return {};
  migrateLegacyThreadId();
  const raw = window.sessionStorage.getItem(THREAD_MAP_KEY);
  if (!raw) return {};
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
    const out: ThreadMap = {};
    for (const [k, v] of Object.entries(parsed as Record<string, unknown>)) {
      if (typeof k === "string" && typeof v === "string" && v.length > 0) out[k] = v;
    }
    return out;
  } catch {
    return {};
  }
}

function writeRawMap(map: ThreadMap): void {
  if (!isBrowser) return;
  if (Object.keys(map).length === 0) {
    window.sessionStorage.removeItem(THREAD_MAP_KEY);
  } else {
    window.sessionStorage.setItem(THREAD_MAP_KEY, JSON.stringify(map));
  }
}

export function loadThreadMap(): ThreadMap {
  return readRawMap();
}

export function saveThreadMapEntry(curriculumId: string, threadId: string): void {
  if (!isBrowser || !curriculumId || !threadId) return;
  const next = { ...readRawMap(), [curriculumId]: threadId };
  writeRawMap(next);
  dispatchChange(curriculumId, threadId);
}

export function loadThreadIdForCurriculum(curriculumId: string): string | null {
  if (!isBrowser || !curriculumId) return null;
  return readRawMap()[curriculumId] ?? null;
}

export function clearThreadIdForCurriculum(curriculumId: string): void {
  if (!isBrowser || !curriculumId) return;
  const current = readRawMap();
  if (!(curriculumId in current)) return;
  const next = { ...current };
  delete next[curriculumId];
  writeRawMap(next);
  dispatchChange(curriculumId, "");
}

export function clearAllThreadMappings(): void {
  if (!isBrowser) return;
  writeRawMap({});
  dispatchChange("*", "");
}

// Back-compat wrappers consumed by components outside `app/session/` (dashboard
// and settings) that this task may not edit. They operate on the entry for the
// *active* curriculum, falling back to a no-op when no curriculum is set.
export function loadThreadId(): string | null {
  if (!isBrowser) return null;
  const active = loadActiveCurriculum();
  if (!active) return null;
  return readRawMap()[active.curriculum_id] ?? null;
}

export function clearThreadId(): void {
  if (!isBrowser) return;
  const active = loadActiveCurriculum();
  if (!active) return;
  clearThreadIdForCurriculum(active.curriculum_id);
}
