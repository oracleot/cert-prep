"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  dashboardSummaryRequest,
  onboardingStateRequest,
  startOnboardingRequest,
} from "./onboarding-api";
import { loadOnboardingId, saveOnboardingId } from "./onboarding-persistence";
import { getAnonymousUserId } from "@/lib/anonymous-user";
import type { AgentFeedEvent, DomainPlan, LearningStyle } from "@/lib/types";

type Step = "welcome" | "exam" | "style" | "feed" | "plan";

function openFeed(
  onboardingId: string,
  onEvent: (event: AgentFeedEvent) => void,
  onComplete: () => void,
) {
  const source = new EventSource(`/api/onboarding/feed?onboarding_id=${onboardingId}`);
  source.onmessage = (message) => {
    const event = JSON.parse(message.data) as AgentFeedEvent;
    onEvent(event);
    if (event.agent === "Curriculum Builder" && event.status === "complete") {
      source.close();
      onComplete();
    }
  };
  return source;
}

export function useOnboarding() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("welcome");
  const [examName, setExamName] = useState("DVA-C02");
  const [learningStyle, setLearningStyle] = useState<LearningStyle>("mixed_review");
  const [events, setEvents] = useState<AgentFeedEvent[]>([]);
  const [domains, setDomains] = useState<DomainPlan[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const feedRef = useRef<EventSource | null>(null);

  const loadPlan = useCallback(async (userId: string) => {
    const res = await dashboardSummaryRequest(userId);
    if (!res.ok) return false;
    const summary = await res.json();
    setDomains(summary.domains || []);
    setStep("plan");
    return true;
  }, []);

  const connectFeed = useCallback((onboardingId: string, userId: string) => {
    feedRef.current?.close();
    feedRef.current = openFeed(
      onboardingId,
      (event) => {
        setEvents((current) => {
          if (event.id && current.some((item) => item.id === event.id)) return current;
          return [...current, event];
        });
      },
      () => void loadPlan(userId),
    );
  }, [loadPlan]);

  useEffect(() => {
    let active = true;
    const userId = getAnonymousUserId();

    async function restore() {
      try {
        const res = await onboardingStateRequest(userId);
        const data = res.ok ? await res.json() : null;
        if (!active) return;

        if (data?.curriculum) {
          router.replace("/dashboard");
          return;
        }

        const onboardingId = data?.run?.id || loadOnboardingId();
        if (onboardingId) {
          saveOnboardingId(onboardingId);
          setStep("feed");
          connectFeed(onboardingId, userId);
        }
      } finally {
        if (active) setIsLoading(false);
      }
    }

    void restore();
    return () => {
      active = false;
      feedRef.current?.close();
    };
  }, [connectFeed, loadPlan, router]);

  async function start() {
    setError("");
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

  return {
    step,
    setStep,
    examName,
    setExamName,
    learningStyle,
    setLearningStyle,
    events,
    domains,
    error,
    isLoading,
    start,
  };
}
