// POST /api/rex/rechallenge
// Returns a harder Rex challenge after Sage has responded.
// Expects: { domain, previousTopic, difficulty }

import { type NextRequest, NextResponse } from "next/server";
import { callOpenRouterJson } from "@/lib/openrouter-json";
import { buildRexRechallengePrompt, MODEL } from "@/agents/prompts/rex";
import type { Challenge } from "@/lib/types";

export async function POST(req: NextRequest) {
  let domain = "Deployment";
  let previousTopic = "";
  let difficulty: "easy" | "medium" | "hard" = "hard";

  try {
    const body = (await req.json()) as {
      domain?: string;
      previousTopic?: string;
      difficulty?: "easy" | "medium" | "hard";
    };
    if (body.domain) domain = body.domain;
    if (body.previousTopic) previousTopic = body.previousTopic;
    if (body.difficulty) difficulty = body.difficulty;
  } catch {
    // Use defaults
  }

  const { system, user } = buildRexRechallengePrompt({
    domain,
    previousTopic,
    difficulty,
  });

  const result = await callOpenRouterJson<Challenge>({
    model: MODEL,
    systemPrompt: system,
    userMessage: user,
    temperature: 0.8,
    maxTokens: 512,
  });

  if (!result.ok) {
    console.error("[rex/rechallenge] OpenRouter error:", result.error);
    return NextResponse.json(
      { error: "Failed to generate rechallenge", details: result.error },
      { status: 502 },
    );
  }

  const challenge = result.data;

  if (
    !challenge.domain ||
    !challenge.topic ||
    !challenge.scenario ||
    !challenge.question
  ) {
    console.error("[rex/rechallenge] Invalid challenge shape:", challenge);
    return NextResponse.json(
      { error: "Rex returned an invalid rechallenge shape" },
      { status: 502 },
    );
  }

  if (process.env.NODE_ENV === "development") {
    console.log("[rex/rechallenge] Generated harder challenge:", {
      domain: challenge.domain,
      topic: challenge.topic,
    });
  }

  return NextResponse.json(challenge);
}
