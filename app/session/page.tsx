"use client";

import { Suspense, useCallback, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { useSession } from "./use-session";
import { ChallengeCard } from "@/components/session/challenge-card";
import { AnswerForm } from "@/components/session/answer-form";
import { SageCard } from "@/components/session/sage-card";
import { SessionErrorView, SessionSummaryView } from "@/components/session/session-overlay";
import { deriveReviewNext } from "@/lib/review-next";
import { OPTION_LABELS } from "@/lib/types";

export default function SessionPage() {
  return (
    <Suspense fallback={null}>
      <SessionContent />
    </Suspense>
  );
}

function SessionContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const focusDomain = searchParams.get("focus_domain")?.trim() ?? "";
  const mode = (searchParams.get("mode") === "review" ? "review" : "new") as "new" | "review";
  const conceptId = searchParams.get("concept_id")?.trim() ?? "";
  const clearFocusDomain = useCallback(() => {
    if (focusDomain) router.replace("/session", { scroll: false });
  }, [focusDomain, router]);
  const {
    phase, cycle, maxCycles, domain, challenge, answer, setAnswer, evaluation,
    sageText, sageCitations, sageFeedback, results, rexRecord, errorMsg,
    submitAnswer, submitSageFeedback, nextChallenge, retry, restart, optionSelection,
  } = useSession(focusDomain, clearFocusDomain, { mode, conceptId });

  const reviewNext = useMemo(() => deriveReviewNext(challenge), [challenge]);

  if (phase === "summary") {
    return <SessionSummaryView results={results} domain={domain} onRestart={restart} />;
  }
  if (phase === "error") {
    return <SessionErrorView errorMsg={errorMsg} onRetry={retry} />;
  }

  const isLoading = phase === "loading_challenge" || phase === "loading_rechallenge";
  const isEvaluating = phase === "evaluating";
  const isStreaming = phase === "streaming_sage";
  const answerDisabled = isEvaluating || isStreaming || phase === "sage_done";
  const cycleProgress = Math.min(100, Math.max(0, (cycle / maxCycles) * 100));
  const showAnswerForm = (phase === "ready" || answerDisabled) && !isLoading;
  const showSage = Boolean(sageText || isStreaming);
  const isOptionBased = optionSelection.isOptionBased;
  const isOptionLocked = isEvaluating || isStreaming || optionSelection.isSubmitted;
  const canSubmitOptions = optionSelection.canSubmit && !isOptionLocked;
  const challengeHasOptions =
    Boolean(challenge?.options) &&
    Array.isArray(challenge?.options) &&
    (challenge?.options?.length ?? 0) === OPTION_LABELS.length;

  return (
    <main className="relative min-h-screen overflow-hidden bg-background px-4 py-10 text-foreground">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(251,191,36,0.18),transparent_32%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.12),transparent_32%)] dark:bg-[radial-gradient(circle_at_20%_10%,rgba(251,191,36,0.18),transparent_32%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.14),transparent_32%)]" />
      <div className="relative mx-auto grid w-full max-w-6xl gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(360px,0.85fr)] lg:items-start">
        <section className="space-y-5" aria-label="Challenge and answer">
          <div className="rounded-3xl border border-zinc-200 bg-white/75 p-4 shadow-sm backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-950/70">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="text-[0.65rem] font-semibold uppercase tracking-[0.3em] text-zinc-500 dark:text-zinc-500">
                  Session domain
                </p>
                <h1 className="mt-1 truncate text-2xl font-black tracking-tight text-zinc-950 dark:text-zinc-50">
                  {domain}
                </h1>
              </div>
              <div className="shrink-0 rounded-2xl bg-zinc-950 px-4 py-3 text-right text-zinc-50 shadow-lg shadow-zinc-950/10 dark:bg-zinc-50 dark:text-zinc-950">
                <p className="text-[0.6rem] font-semibold uppercase tracking-[0.25em] opacity-60">
                  Score
                </p>
                <p className="mt-1 text-xl font-black leading-none">
                  {rexRecord.user_wins}-{rexRecord.rex_wins}
                </p>
                <p className="mt-1 text-[0.6rem] font-semibold uppercase tracking-[0.2em] opacity-70">
                  You vs Rex
                </p>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-3">
              <span className="rounded-full bg-amber-300 px-3 py-1 text-xs font-black uppercase tracking-wider text-zinc-950">
                Cycle {cycle}
              </span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
                <div
                  className="h-full rounded-full bg-amber-300"
                  style={{ width: `${cycleProgress}%` }}
                />
              </div>
              <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                of {maxCycles}
              </span>
            </div>
          </div>

          <ChallengeCard
            challenge={challenge}
            isLoading={isLoading}
            verdict={evaluation}
            selectedLabels={optionSelection.selectedLabels}
            isLocked={isOptionLocked}
            onToggleLabel={optionSelection.toggleLabel}
          />

          {showAnswerForm && (
            <AnswerForm
              value={answer}
              onChange={setAnswer}
              onSubmit={submitAnswer}
              onKnowledgeGap={() => submitAnswer("knowledge_gap")}
              isDisabled={answerDisabled}
              isEvaluating={isEvaluating}
              optionBased={isOptionBased && challengeHasOptions}
              optionHint={
                challenge?.response_mode === "multiple_response"
                  ? "Pick the options you think are correct, then submit."
                  : "Pick the option you think is correct, then submit."
              }
              canSubmitOptions={canSubmitOptions}
            />
          )}
        </section>

        <aside className="lg:sticky lg:top-10" aria-label="Sage response">
          {showSage ? (
            <SageCard
              text={sageText}
              citations={sageCitations}
              isStreaming={isStreaming}
              outcome={evaluation?.outcome ?? null}
              answerIntent={evaluation?.answer_intent ?? "attempt"}
              cycle={cycle}
              maxCycles={maxCycles}
              feedback={sageFeedback}
              reviewNext={reviewNext}
              onNext={nextChallenge}
              onFeedbackSubmit={submitSageFeedback}
              evaluation={evaluation}
              isOptionBased={challengeHasOptions}
            />
          ) : (
            <div className="min-h-[320px] rounded-2xl border border-dashed border-zinc-300 bg-white/55 p-6 backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-950/50">
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-zinc-500">
                Sage
              </p>
              <div className="mt-20 max-w-sm">
                <h2 className="text-2xl font-black tracking-tight text-zinc-950 dark:text-zinc-50">
                  Answer first. Then Sage cuts through the fog.
                </h2>
                <p className="mt-3 text-sm leading-relaxed text-zinc-600 dark:text-zinc-300">
                  Submit your response on the left. Sage&apos;s explanation, corrections,
                  and sources will stay pinned here while the next challenge loads.
                </p>
              </div>
            </div>
          )}
        </aside>
      </div>
    </main>
  );
}