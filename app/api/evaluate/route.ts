// POST /api/evaluate
// Evaluates a user's answer to a Rex challenge.
// Returns: { outcome: "correct" | "incorrect", reasoning: string }

import { type NextRequest, NextResponse } from "next/server";
import { callOpenRouterJson } from "@/lib/openrouter-json";
import { buildEvaluatorPrompt, MODEL } from "@/agents/prompts/evaluator";
import type { Challenge, EvaluationResult } from "@/lib/types";

export async function POST(req: NextRequest) {
  let challenge: Challenge;
  let userAnswer: string;

  try {
    const body = (await req.json()) as {
      challenge: Challenge;
      userAnswer: string;
    };

    if (
      !body.challenge?.domain ||
      !body.challenge?.scenario ||
      !body.challenge?.question ||
      !body.userAnswer?.trim()
    ) {
      return NextResponse.json(
        { error: "Missing required fields: challenge and userAnswer" },
        { status: 400 },
      );
    }

    challenge = body.challenge;
    userAnswer = body.userAnswer;
  } catch {
    return NextResponse.json({ error: "Invalid request body" }, { status: 400 });
  }

  const { system, user } = buildEvaluatorPrompt({
    domain: challenge.domain,
    topic: challenge.topic,
    scenario: challenge.scenario,
    question: challenge.question,
    userAnswer,
  });

  const result = await callOpenRouterJson<EvaluationResult>({
    model: MODEL,
    systemPrompt: system,
    userMessage: user,
    temperature: 0.2,
    maxTokens: 256,
  });

  if (!result.ok) {
    console.error("[evaluate] OpenRouter error:", result.error);
    return NextResponse.json(
      { error: "Evaluation failed", details: result.error },
      { status: 502 },
    );
  }

  const evaluation = result.data;

  if (
    evaluation.outcome !== "correct" &&
    evaluation.outcome !== "incorrect"
  ) {
    console.error("[evaluate] Invalid outcome:", evaluation);
    return NextResponse.json(
      { error: "Evaluator returned invalid outcome" },
      { status: 502 },
    );
  }

  // Dev logging per AC 1.5
  if (process.env.NODE_ENV === "development") {
    console.log("[evaluate] Result:", evaluation.outcome, "|", evaluation.reasoning);
  }

  return NextResponse.json(evaluation);
}
