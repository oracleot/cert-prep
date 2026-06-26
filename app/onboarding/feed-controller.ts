"use client";

import { useCallback, useRef, type Dispatch, type SetStateAction } from "react";

import { onboardingStateRequest } from "./onboarding-api";
import { openOnboardingFeed, type FeedIssue } from "@/lib/onboarding-feed";
import type { AgentFeedEvent } from "@/lib/types";

const STALE_FEED_MS = 60_000;

type Args = {
  setFeedIssue: Dispatch<SetStateAction<FeedIssue | null>>;
  setEvents: Dispatch<SetStateAction<AgentFeedEvent[]>>;
  loadPlan: (userId: string) => Promise<boolean>;
};

/**
 * Owns the SSE feed lifecycle for an in-flight onboarding build.
 * Extracted from use-onboarding so the hook can stay under the
 * 200-line file limit while picking up the Settings prefill banner.
 */
export function useFeedController({ setFeedIssue, setEvents, loadPlan }: Args) {
  const feedRef = useRef<EventSource | null>(null);
  const staleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearStaleTimer = useCallback(() => {
    if (!staleTimerRef.current) return;
    clearTimeout(staleTimerRef.current);
    staleTimerRef.current = null;
  }, []);

  const reconcileFeed = useCallback(
    async (onboardingId: string, userId: string) => {
      const res = await onboardingStateRequest(userId);
      const data = res.ok ? await res.json() : null;
      if (data?.run?.id === onboardingId && data.run.status === "complete") {
        await loadPlan(userId);
        return;
      }
      setFeedIssue({
        message: data?.run?.status === "failed"
          ? "The build failed. Try again with the same choices."
          : "The build is taking longer than expected. Try again.",
        action: "build",
      });
    },
    [loadPlan, setFeedIssue],
  );

  const connectFeed = useCallback(
    (onboardingId: string, userId: string) => {
      const resetStaleTimer = () => {
        clearStaleTimer();
        staleTimerRef.current = setTimeout(() => {
          feedRef.current?.close();
          void reconcileFeed(onboardingId, userId);
        }, STALE_FEED_MS);
      };

      feedRef.current?.close();
      resetStaleTimer();
      feedRef.current = openOnboardingFeed(onboardingId, {
        onEvent: (event) => {
          setFeedIssue(null);
          resetStaleTimer();
          setEvents((current) => {
            if (event.id && current.some((item) => item.id === event.id)) return current;
            return [...current, event];
          });
        },
        onComplete: () => {
          clearStaleTimer();
          void loadPlan(userId);
        },
        onFailure: (message) => {
          clearStaleTimer();
          setFeedIssue({ message, action: "build" });
        },
        onError: () => {
          clearStaleTimer();
          void reconcileFeed(onboardingId, userId);
        },
      });
    },
    [clearStaleTimer, loadPlan, reconcileFeed, setEvents, setFeedIssue],
  );

  const disconnect = useCallback(() => {
    feedRef.current?.close();
    clearStaleTimer();
  }, [clearStaleTimer]);

  return { connectFeed, reconcileFeed, disconnect };
}
