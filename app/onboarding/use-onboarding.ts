"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  dashboardSummaryRequest,
  onboardingStateRequest,
  startOnboardingRequest,
  supportedExamsRequest,
} from "./onboarding-api";
import { useFeedController } from "./feed-controller";
import { loadOnboardingId, saveOnboardingId } from "./onboarding-persistence";
import { getAnonymousUserId } from "@/lib/anonymous-user";
import { getExamName } from "@/lib/exam-names";
import type { FeedIssue } from "@/lib/onboarding-feed";
import type { AgentFeedEvent, DomainPlan, ExamOption, LearningStyle } from "@/lib/types";

type Step = "welcome" | "exam" | "style" | "feed" | "plan";

type SettingsPreflight = { examId: string; examName: string };

function readSettingsPreflight(): SettingsPreflight | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  if (params.get("source") !== "settings") return null;
  const examId = params.get("exam");
  if (!examId) return null;
  return { examId, examName: getExamName(examId) };
}

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
  const [preflight, setPreflight] = useState<SettingsPreflight | null>(null);

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

  const { connectFeed, disconnect } = useFeedController({ setFeedIssue, setEvents, loadPlan });

  useEffect(() => {
    let active = true;
    const userId = getAnonymousUserId();

    async function restore() {
      try {
        const preflightParams = readSettingsPreflight();
        if (preflightParams) setPreflight(preflightParams);

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
        } else if (preflightParams) {
          // No existing run — apply URL prefill so the chosen exam is pre-selected.
          setExamName(preflightParams.examId);
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
      disconnect();
    };
  }, [connectFeed, disconnect, loadPlan, router]);

  async function start() {
    setError("");
    setFeedIssue(null);
    disconnect();
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
    preflight,
    start,
    retryPlan,
  };
}
