// POST /api/sage
// Streams Sage's response via SSE.
// Routes to sage_depth (correct) or sage_explain (incorrect) based on outcome.

import { type NextRequest } from "next/server";
import { streamOpenRouterResponse, sseResponseFromStream, openRouterErrorToSseResponse } from "@/lib/openrouter";
import { buildSageDepthPrompt, buildSageExplainPrompt, MODEL } from "@/agents/prompts/sage";
import type { Challenge, EvaluationResult } from "@/lib/types";

export async function POST(req: NextRequest) {
  let challenge: Challenge;
  let evaluation: EvaluationResult;
  let userAnswer: string;

  try {
    const body = (await req.json()) as {
      challenge: Challenge;
      evaluation: EvaluationResult;
      userAnswer: string;
    };

    if (
      !body.challenge?.domain ||
      !body.evaluation?.outcome ||
      !body.userAnswer
    ) {
      return new Response(JSON.stringify({ error: "Missing required fields" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    challenge = body.challenge;
    evaluation = body.evaluation;
    userAnswer = body.userAnswer;
  } catch {
    return new Response(JSON.stringify({ error: "Invalid request body" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const sageInput = {
    domain: challenge.domain,
    topic: challenge.topic,
    scenario: challenge.scenario,
    question: challenge.question,
    userAnswer,
    reasoning: evaluation.reasoning,
  };

  const { system, user } =
    evaluation.outcome === "correct"
      ? buildSageDepthPrompt(sageInput)
      : buildSageExplainPrompt(sageInput);

  const result = await streamOpenRouterResponse({
    model: MODEL,
    systemPrompt: system,
    userMessage: user,
    temperature: 0.7,
    maxTokens: 512,
  });

  if (!result.ok) {
    console.error("[sage] OpenRouter error:", result.error);
    return openRouterErrorToSseResponse(result.error);
  }

  return sseResponseFromStream(result.stream);
}
