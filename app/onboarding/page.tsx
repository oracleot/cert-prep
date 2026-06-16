"use client";

import { AgentFeed } from "@/components/onboarding/agent-feed";
import { ExamStep } from "@/components/onboarding/exam-step";
import { PlanReveal } from "@/components/onboarding/plan-reveal";
import { StyleStep } from "@/components/onboarding/style-step";
import { WelcomeStep } from "@/components/onboarding/welcome-step";

import { useOnboarding } from "./use-onboarding";

export default function OnboardingPage() {
  const onboarding = useOnboarding();

  return (
    <main className="min-h-screen overflow-hidden bg-black px-4 py-6 text-zinc-50 sm:px-6 lg:px-8">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(251,191,36,0.22),transparent_28%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.16),transparent_30%)]" />
      <div className="relative mx-auto flex min-h-[calc(100vh-3rem)] w-full max-w-5xl items-center">
        <div className="w-full">
          <div className="mb-5 flex items-center justify-between text-xs uppercase tracking-[0.35em] text-zinc-500">
            <span>Gauntlet</span>
            <span>{onboarding.step}</span>
          </div>

          {onboarding.step === "welcome" ? (
            <WelcomeStep onContinue={() => onboarding.setStep("exam")} />
          ) : null}
          {onboarding.step === "exam" ? (
            <ExamStep
              examName={onboarding.examName}
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
          {onboarding.step === "feed" ? <AgentFeed events={onboarding.events} /> : null}
          {onboarding.step === "plan" ? <PlanReveal domains={onboarding.domains} /> : null}
        </div>
      </div>
    </main>
  );
}
