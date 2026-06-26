"use client";

import { useEffect } from "react";

import { AgentFeed } from "@/components/onboarding/agent-feed";
import { ExamStep } from "@/components/onboarding/exam-step";
import { PlanReveal } from "@/components/onboarding/plan-reveal";
import { StyleStep } from "@/components/onboarding/style-step";
import { WelcomeStep } from "@/components/onboarding/welcome-step";

import { useOnboarding } from "./use-onboarding";

export default function OnboardingPage() {
  const onboarding = useOnboarding();

  // Settings prefill flow: once the build lands, bounce back so the user
  // can continue swapping or starting a session from /settings.
  useEffect(() => {
    if (onboarding.source === "settings" && onboarding.step === "plan") {
      window.location.href = "/settings";
    }
  }, [onboarding.source, onboarding.step]);

  if (onboarding.isLoading) {
    return (
      <main className="min-h-screen bg-background px-4 py-6 text-foreground sm:px-6 lg:px-8" />
    );
  }

  return (
    <main className="min-h-screen overflow-hidden bg-background px-4 py-6 text-foreground sm:px-6 lg:px-8">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(251,191,36,0.18),transparent_30%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.12),transparent_32%)] dark:bg-[radial-gradient(circle_at_20%_10%,rgba(251,191,36,0.22),transparent_28%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.16),transparent_30%)]" />
      <div className="relative mx-auto flex min-h-[calc(100vh-3rem)] w-full max-w-5xl items-center">
        <div className="w-full">
          <div className="mb-5 flex items-center justify-between text-xs uppercase tracking-[0.35em] text-muted-foreground">
            <span>Gauntlet</span>
            <span>{onboarding.step}</span>
          </div>

          {onboarding.preflight ? (
            <div className="mb-5 rounded-2xl border border-amber-300 bg-amber-100/80 px-5 py-4 text-sm font-bold text-amber-900 dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-100" role="status">
              Building curriculum for {onboarding.preflight.examName}. Complete onboarding to activate.
            </div>
          ) : null}

          {onboarding.step === "welcome" ? (
            <WelcomeStep onContinue={() => onboarding.setStep(onboarding.nextStep)} />
          ) : null}
          {onboarding.step === "exam" ? (
            <ExamStep
              examName={onboarding.examName}
              examOptions={onboarding.examOptions}
              onChange={onboarding.setExamName}
              onBack={() => onboarding.setStep("welcome")}
              onContinue={() => onboarding.setStep("style")}
              error={onboarding.error}
            />
          ) : null}
          {onboarding.step === "style" ? (
            <StyleStep
              value={onboarding.learningStyle}
              onChange={onboarding.setLearningStyle}
              onBack={() => onboarding.setStep("exam")}
              onStart={onboarding.start}
              isLoading={onboarding.isLoading}
            />
          ) : null}
          {onboarding.step === "feed" ? (
            <AgentFeed
              events={onboarding.events}
              issue={onboarding.feedIssue}
              onRetryBuild={onboarding.start}
              onRetryPlan={onboarding.retryPlan}
              onBack={() => onboarding.setStep("style")}
            />
          ) : null}
          {onboarding.step === "plan" ? (
            <PlanReveal domains={onboarding.domains} source={onboarding.source} />
          ) : null}
        </div>
      </div>
    </main>
  );
}
