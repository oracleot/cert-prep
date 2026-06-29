"use client";
import { useCallback, useEffect, useRef } from "react";
import { clearActiveThreadId } from "./session-scope";

type LifecycleDeps = {
  startSession: (manual: boolean) => Promise<void>;
  restoreSession: (threadId: string, manual: boolean) => Promise<unknown>;
  clearThread: () => void;
  bumpRequest: () => void;
  onFocusDomainConsumed?: () => void;
  resumableThreadId: string | null;
  startOverrides: { mode?: "new" | "review"; conceptId?: string };
};

export function useSessionLifecycle(deps: LifecycleDeps): { abandonSession: () => void } {
  const { startSession, restoreSession, clearThread, bumpRequest, onFocusDomainConsumed, resumableThreadId, startOverrides } = deps;
  const reviewLaunchedRef = useRef(false);

  const abandonSession = useCallback(() => {
    bumpRequest();
    clearActiveThreadId();
    clearThread();
  }, [bumpRequest, clearThread]);

  useEffect(() => {
    const saved = resumableThreadId;
    const reviewOverride = startOverrides.mode === "review";
    // Reset the launch guard whenever mode leaves "review", so a later new-mode
    // session can still be started normally, and a return to "review" can fire.
    if (!reviewOverride) reviewLaunchedRef.current = false;
    queueMicrotask(() => {
      if (reviewOverride) {
        if (reviewLaunchedRef.current) return; // already in-flight
        reviewLaunchedRef.current = true;
        // Review sessions are always fresh — never resume a thread that was
        // started in a different mode (URL params would be silently dropped).
        if (saved) clearActiveThreadId();
        return void startSession(false);
      }
      if (!saved) return void startSession(false);
      onFocusDomainConsumed?.();
      void restoreSession(saved, false).then((p) => p === null && void startSession(false));
    });
  }, [restoreSession, startSession, onFocusDomainConsumed, resumableThreadId, startOverrides.mode, startOverrides.conceptId]);

  return { abandonSession };
}