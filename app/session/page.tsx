"use client";

// Session screen — full-focus Rex + Sage loop
// AC 1.4, 1.7: no navigation visible; mobile-first

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
    restart,
  } = useSession();

  if (phase === "summary") {
    return (
      <main className="flex min-h-screen items-start justify-center bg-background px-4 py-12">
        <div className="w-full max-w-lg">
          <SummaryScreen results={results} domain={domain} onRestart={restart} />
        </div>
      </main>
    );
  }

  if (phase === "error") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background px-4">
        <div className="w-full max-w-lg rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-center">
          <p className="text-sm font-medium text-destructive">{errorMsg}</p>
          <button
            onClick={restart}
            className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
          >
            Try again
          </button>
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
    <main className="flex min-h-screen items-start justify-center bg-background px-4 py-12">
      <div className="w-full max-w-lg space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            {domain}
          </span>
          <span className="text-xs text-muted-foreground">
            Cycle {cycle} of {maxCycles}
          </span>
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
