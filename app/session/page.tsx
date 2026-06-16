"use client";

import { useSession } from "./use-session";
import { ChallengeCard } from "@/components/session/challenge-card";
import { AnswerForm } from "@/components/session/answer-form";
import { SageCard } from "@/components/session/sage-card";
import { SummaryScreen } from "@/components/session/summary-screen";

export default function SessionPage() {
  const {
    phase,
    cycle,
    maxCycles,
    domain,
    challenge,
    answer,
    setAnswer,
    evaluation,
    sageText,
    results,
    errorMsg,
    submitAnswer,
    nextChallenge,
    retry,
    restart,
  } = useSession();

  if (phase === "summary") {
    return (
      <main className="relative min-h-screen overflow-hidden bg-background px-4 py-12 text-foreground">
        <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(251,191,36,0.18),transparent_32%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.12),transparent_32%)] dark:bg-[radial-gradient(circle_at_20%_10%,rgba(251,191,36,0.18),transparent_32%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.14),transparent_32%)]" />
        <div className="relative mx-auto flex w-full max-w-lg items-start justify-center">
          <SummaryScreen results={results} domain={domain} onRestart={restart} />
        </div>
      </main>
    );
  }

  if (phase === "error") {
    return (
      <main className="relative min-h-screen overflow-hidden bg-background px-4 text-foreground">
        <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(251,191,36,0.18),transparent_32%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.12),transparent_32%)] dark:bg-[radial-gradient(circle_at_20%_10%,rgba(251,191,36,0.18),transparent_32%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.14),transparent_32%)]" />
        <div className="relative flex min-h-screen items-center justify-center">
          <div className="w-full max-w-lg rounded-2xl border border-rose-500/30 bg-rose-500/5 p-6 text-center backdrop-blur-sm">
            <p className="text-sm font-medium text-rose-700 dark:text-rose-200">{errorMsg}</p>
            <button
              onClick={retry}
              className="mt-4 min-h-11 rounded-full bg-amber-300 px-5 text-sm font-black text-zinc-950 hover:bg-amber-200"
            >
              Retry
            </button>
          </div>
        </div>
      </main>
    );
  }

  const isLoading =
    phase === "loading_challenge" || phase === "loading_rechallenge";
  const isEvaluating = phase === "evaluating";
  const isStreaming = phase === "streaming_sage";
  const answerDisabled = isEvaluating || isStreaming || phase === "sage_done";

  return (
    <main className="relative min-h-screen overflow-hidden bg-background px-4 py-10 text-foreground">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(251,191,36,0.18),transparent_32%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.12),transparent_32%)] dark:bg-[radial-gradient(circle_at_20%_10%,rgba(251,191,36,0.18),transparent_32%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.14),transparent_32%)]" />
      <div className="relative mx-auto w-full max-w-lg space-y-5">
        <div className="flex items-center justify-between text-[0.7rem] font-semibold uppercase tracking-[0.35em] text-zinc-600 dark:text-zinc-500">
          <span>{domain}</span>
          <span>Cycle {cycle} of {maxCycles}</span>
        </div>

        <ChallengeCard challenge={challenge} isLoading={isLoading} />

        {(phase === "ready" || answerDisabled) && !isLoading && (
          <AnswerForm
            value={answer}
            onChange={setAnswer}
            onSubmit={submitAnswer}
            isDisabled={answerDisabled}
            isEvaluating={isEvaluating}
          />
        )}

        {(sageText || isStreaming) && (
          <SageCard
            text={sageText}
            isStreaming={isStreaming}
            outcome={evaluation?.outcome ?? null}
            cycle={cycle}
            maxCycles={maxCycles}
            onNext={nextChallenge}
          />
        )}
      </div>
    </main>
  );
}
