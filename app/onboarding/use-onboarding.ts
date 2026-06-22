"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  dashboardSummaryRequest,
  onboardingStateRequest,
  startOnboardingRequest,
  supportedExamsRequest,
} from "./onboarding-api";
import { loadOnboardingId, saveOnboardingId } from "./onboarding-persistence";
import { getAnonymousUserId } from "@/lib/anonymous-user";
import { openOnboardingFeed, type FeedIssue } from "@/lib/onboarding-feed";
import type { AgentFeedEvent, DomainPlan, ExamOption, LearningStyle } from "@/lib/types";

type Step = "welcome" | "exam" | "style" | "feed" | "plan";

const STALE_FEED_MS = 60_000;

export function useOnboarding() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("welcome");
  const [examName, setExamName] = useState("");
  const [learningStyle, setLearningStyle] = useState<LearningStyle>("mixed_review");
  const [events, setEvents] = useState<AgentFeedEvent[]>([]);
  const [domains, setDomains] = useState<DomainPlan[]>([]);
  const [examOptions, setExamOptions] = useState<ExamOption[]>([]);
  const [error, setError] = useState("");
  const [feedIssue, setFeedIssue] = useState<FeedIssue | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const feedRef = useRef<EventSource | null>(null);
  const staleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearStaleTimer = useCallback(() => {
    if (!staleTimerRef.current) return;
    clearTimeout(staleTimerRef.current);
    staleTimerRef.current = null;
  }, []);

  const loadPlan = useCallback(async (userId: string) => {
    const res = await dashboardSummaryRequest(userId);
    if (!res.ok) {
      setFeedIssue({
        message: "Your plan was built, but the summary could not load.",
        action: "plan",
      });
      return false;
    }
    const summary = await res.json();
    setDomains(summary.domains || []);
    setFeedIssue(null);
    setStep("plan");
    return true;
  }, []);

  const reconcileFeed = useCallback(async (onboardingId: string, userId: string) => {
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
  }, [loadPlan]);

  const connectFeed = useCallback((onboardingId: string, userId: string) => {
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
  }, [clearStaleTimer, loadPlan, reconcileFeed]);

  useEffect(() => {
    let active = true;
    const userId = getAnonymousUserId();

    async function restore() {
      try {
        const examsRes = await supportedExamsRequest();
        if (examsRes.ok) setExamOptions((await examsRes.json()).exams || []);
        const res = await onboardingStateRequest(userId);
        const data = res.ok ? await res.json() : null;
        if (!active) return;

        const savedOnboardingId = loadOnboardingId();
        const onboardingId = data?.run?.id || savedOnboardingId;
        if (data?.run) {
          setExamName(data.run.exam_name || "");
          setLearningStyle(data.run.learning_style || "mixed_review");
        }
        if (data?.run && onboardingId && data.run.status !== "complete") {
          saveOnboardingId(onboardingId);
          setStep("feed");
          connectFeed(onboardingId, userId);
          return;
        }

        if (data?.run?.id === savedOnboardingId && data?.curriculum) {
          if (!(await loadPlan(userId))) setStep("feed");
          return;
        }

        if (data?.curriculum) {
          router.replace("/dashboard");
          return;
        }
      } finally {
        if (active) setIsLoading(false);
      }
    }

    void restore();
    return () => {
      active = false;
      feedRef.current?.close();
      clearStaleTimer();
    };
  }, [clearStaleTimer, connectFeed, loadPlan, router]);

  async function start() {
    setError("");
    setFeedIssue(null);
    clearStaleTimer();
    setIsLoading(true);
    const userId = getAnonymousUserId();
    const res = await startOnboardingRequest({
      user_id: userId,
      exam_name: examName,
      learning_style: learningStyle,
    });
    const data = await res.json();
    setIsLoading(false);

    if (!res.ok || !data.accepted) {
      setError(data.message || data.error || "Onboarding could not start.");
      return;
    }

    saveOnboardingId(data.onboarding_id);
    setEvents([]);
    setStep("feed");
    connectFeed(data.onboarding_id, userId);
  }

  function retryPlan() {
    setFeedIssue(null);
    void loadPlan(getAnonymousUserId());
  }

  return {
    step,
    setStep,
    examName,
    setExamName,
    learningStyle,
    setLearningStyle,
    events,
    domains,
    examOptions,
    error,
    feedIssue,
    isLoading,
    start,
    retryPlan,
  };
}
