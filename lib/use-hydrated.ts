"use client";

import { useSyncExternalStore } from "react";

function subscribe(notify: () => void) {
  // Hydration completes when React finishes the initial render on the client.
  // The "false" server snapshot flips to "true" on the client via microtask,
  // so we fire notify once to trigger a re-render with the real state.
  queueMicrotask(notify);
  return () => {};
}

export function useHydrated() {
  return useSyncExternalStore(subscribe, () => true, () => false);
}
