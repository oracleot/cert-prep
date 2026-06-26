"use client";

import { useSyncExternalStore } from "react";

/**
 * Browser-local active-curriculum state.
 *
 * The active curriculum is per-user-per-exam; until Clerk lands in Phase 4
 * it lives in localStorage so any tab (and any task running after a page
 * reload) can read which curriculum should drive /session and /dashboard.
 *
 * Cross-tab sync: the `storage` event. Same-tab sync: a CustomEvent
 * dispatched from the writer so React subscribers re-render immediately
 * without waiting for a reload.
 */

export type ActiveCurriculum = {
  exam_id: string;
  exam_name: string;
  curriculum_id: string;
  saved_at: string;
};

const STORAGE_KEY = "gauntlet.active-curriculum.v1";
const EVENT_NAME = "gauntlet:active-curriculum-changed";
const isBrowser = typeof window !== "undefined";

function read(): ActiveCurriculum | null {
  if (!isBrowser) return null;
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    const parsed: unknown = JSON.parse(raw);
    if (
      parsed &&
      typeof parsed === "object" &&
      typeof (parsed as ActiveCurriculum).exam_id === "string" &&
      typeof (parsed as ActiveCurriculum).exam_name === "string" &&
      typeof (parsed as ActiveCurriculum).curriculum_id === "string" &&
      typeof (parsed as ActiveCurriculum).saved_at === "string"
    ) {
      return parsed as ActiveCurriculum;
    }
    return null;
  } catch {
    return null;
  }
}

export function loadActiveCurriculum(): ActiveCurriculum | null {
  return read();
}

export function saveActiveCurriculum(c: ActiveCurriculum): void {
  if (!isBrowser) return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(c));
  window.dispatchEvent(new CustomEvent<ActiveCurriculum>(EVENT_NAME, { detail: c }));
}

export function clearActiveCurriculum(): void {
  if (!isBrowser) return;
  window.localStorage.removeItem(STORAGE_KEY);
  window.dispatchEvent(new CustomEvent<ActiveCurriculum | null>(EVENT_NAME, { detail: null }));
}

type UseActiveCurriculumResult = {
  active: ActiveCurriculum | null;
  setActive: (c: ActiveCurriculum) => void;
  clear: () => void;
};

function subscribe(notify: () => void): () => void {
  if (!isBrowser) return () => {};
  const onCustom = () => notify();
  const onStorage = (event: StorageEvent) => {
    if (event.key === STORAGE_KEY || event.key === null) notify();
  };
  window.addEventListener(EVENT_NAME, onCustom);
  window.addEventListener("storage", onStorage);
  return () => {
    window.removeEventListener(EVENT_NAME, onCustom);
    window.removeEventListener("storage", onStorage);
  };
}

export function useActiveCurriculum(): UseActiveCurriculumResult {
  const active = useSyncExternalStore(subscribe, read, () => null);
  return {
    active,
    setActive: saveActiveCurriculum,
    clear: clearActiveCurriculum,
  };
}