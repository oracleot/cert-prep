"use client";
// Phase 11 — shared submit-stream consumer.
//
// Used by both the option-based and free-text branches of use-session.
// Wraps the readSessionStream call with consistent accumulator + result-row
// updates so the two branches can stay small.

import { useCallback } from "react";
import type { AnswerIntent, Challenge, EvaluationResult } from "@/lib/types";
import { submitSessionRequest } from "./session-api";
import { readSessionStream } from "./session-stream";
import type { SessionResult } from "@/lib/types";

type SubmitStreamDeps = {
  challenge: Challenge | null;
  threadId: string | null;
  cycle: number;
  setPhase: (p: "evaluating" | "streaming_sage" | "sage_done" | "error") => void;
  setSageCitations: (c: import("@/lib/types").Citation[]) => void;
  setSageText: (s: string) => void;
  setEvaluation: (e: EvaluationResult | null) => void;
  setResults: (updater: (prev: SessionResult[]) => SessionResult[]) => void;
  setErrorMsg: (s: string) => void;
  refreshRexRecord: () => Promise<unknown> | void;
  onLock: () => void;
};

export type SubmitStreamArgs = {
  userAnswer: string;
  answerIntent: AnswerIntent;
  selectedLabels: import("@/lib/types").OptionLabel[];
};

export function useSubmitStream(deps: SubmitStreamDeps) {
  const { challenge, threadId, cycle, refreshRexRecord } = deps;
  return useCallback(
    async (args: SubmitStreamArgs) => {
      if (!challenge || !threadId) return;
      deps.onLock();
      deps.setPhase("evaluating");
      const res = await submitSessionRequest(
        threadId,
        args.userAnswer,
        args.answerIntent,
        args.selectedLabels,
      );
      if (!res.ok || !res.body) {
        deps.setErrorMsg("Evaluation failed. Try again.");
        deps.setPhase("error");
        return;
      }
      let currentEvaluation: EvaluationResult | null = null;
      let accumulated = "";
      deps.setSageCitations([]);
      await readSessionStream(res.body, {
        onEvaluation: (nextEvaluation) => {
          nextEvaluation.answer_intent ??= args.answerIntent;
          currentEvaluation = nextEvaluation;
          deps.setEvaluation(nextEvaluation);
          deps.setPhase("streaming_sage");
        },
        onToken: (token) => {
          accumulated += token;
          deps.setSageText(accumulated);
        },
        onCitations: deps.setSageCitations,
        onDone: () => {
          if (currentEvaluation) {
            deps.setResults((prev) => [
              ...prev,
              {
                cycle,
                topic: challenge.topic,
                outcome: currentEvaluation!.outcome,
                answer_intent: args.answerIntent,
              },
            ]);
          }
          void refreshRexRecord();
          deps.setPhase("sage_done");
        },
        onError: (message) => {
          deps.setErrorMsg(message);
          deps.setPhase("error");
        },
      });
    },
    [challenge, threadId, cycle, refreshRexRecord, deps],
  );
}