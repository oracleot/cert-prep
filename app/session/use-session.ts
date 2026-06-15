"use client";

// Session state hook — orchestrates the Rex + Sage loop
// Phase 1: 2 cycles, hardcoded Deployment domain, in-memory only

import { useState, useCallback, useEffect, useRef } from "react";
import { readSseStream } from "@/lib/sse-reader";
import type { Challenge, EvaluationResult, SessionResult } from "@/lib/types";

export type SessionPhase =
  | "loading_challenge"
  | "ready"
  | "evaluating"
  | "streaming_sage"
  | "sage_done"
  | "loading_rechallenge"
  | "summary"
  | "error";

const DOMAIN = "Deployment";
const MAX_CYCLES = 2;

export function useSession() {
  const [phase, setPhase] = useState<SessionPhase>("loading_challenge");
  const [cycle, setCycle] = useState(1);
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const [answer, setAnswer] = useState("");
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [sageText, setSageText] = useState("");
  const [results, setResults] = useState<SessionResult[]>([]);
  const [errorMsg, setErrorMsg] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  const fetchChallenge = useCallback(async (difficulty: "medium" | "hard" = "medium") => {
    setPhase("loading_challenge");
    setChallenge(null);
    setAnswer("");
    setEvaluation(null);
    setSageText("");

    const res = await fetch("/api/rex/challenge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ domain: DOMAIN, difficulty }),
    });

    if (!res.ok) {
      setErrorMsg("Rex couldn't generate a challenge. Try again.");
      setPhase("error");
      return;
    }

    const data = (await res.json()) as Challenge;
    setChallenge(data);
    setPhase("ready");
  }, []);

  const fetchRechallenge = useCallback(async (previousTopic: string) => {
    setPhase("loading_rechallenge");
    setChallenge(null);
    setAnswer("");
    setEvaluation(null);
    setSageText("");

    const res = await fetch("/api/rex/rechallenge", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ domain: DOMAIN, previousTopic, difficulty: "hard" }),
    });

    if (!res.ok) {
      setErrorMsg("Rex couldn't generate a rechallenge. Try again.");
      setPhase("error");
      return;
    }

    const data = (await res.json()) as Challenge;
    setChallenge(data);
    setPhase("ready");
  }, []);

  const submitAnswer = useCallback(async () => {
    if (!challenge || !answer.trim()) return;

    setPhase("evaluating");

    const evalRes = await fetch("/api/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ challenge, userAnswer: answer }),
    });

    if (!evalRes.ok) {
      setErrorMsg("Evaluation failed. Try again.");
      setPhase("error");
      return;
    }

    const evalData = (await evalRes.json()) as EvaluationResult;
    setEvaluation(evalData);
    setPhase("streaming_sage");

    // Stream Sage response
    abortRef.current = new AbortController();
    const sageRes = await fetch("/api/sage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ challenge, evaluation: evalData, userAnswer: answer }),
      signal: abortRef.current.signal,
    });

    if (!sageRes.ok || !sageRes.body) {
      setErrorMsg("Sage failed to respond. Try again.");
      setPhase("error");
      return;
    }

    await readSseStream(sageRes.body, (event) => {
      if (event.type === "token") {
        setSageText((prev) => prev + event.token);
      } else if (event.type === "done") {
        setResults((prev) => [
          ...prev,
          { cycle, topic: challenge.topic, outcome: evalData.outcome },
        ]);
        setPhase("sage_done");
      } else if (event.type === "error") {
        setErrorMsg(event.error.message);
        setPhase("error");
      }
    });
  }, [challenge, answer, cycle]);

  const nextChallenge = useCallback(async () => {
    if (!challenge) return;

    if (cycle >= MAX_CYCLES) {
      setPhase("summary");
      return;
    }

    const nextCycle = cycle + 1;
    setCycle(nextCycle);
    await fetchRechallenge(challenge.topic);
  }, [challenge, cycle, fetchRechallenge]);

  const restart = useCallback(() => {
    setCycle(1);
    setResults([]);
    setErrorMsg("");
    fetchChallenge("medium");
  }, [fetchChallenge]);

  // Initial load
  useEffect(() => {
    fetchChallenge("medium");
  }, [fetchChallenge]);

  return {
    phase,
    cycle,
    maxCycles: MAX_CYCLES,
    domain: DOMAIN,
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
  };
}
