// POST /api/rex/challenge
// Returns a structured certification challenge JSON from Rex.
// Phase 1: domain hardcoded to "Deployment"

import { type NextRequest, NextResponse } from "next/server";
import { callOpenRouterJson } from "@/lib/openrouter-json";
import { buildRexChallengePrompt, MODEL } from "@/agents/prompts/rex";
import type { Challenge } from "@/lib/types";

export async function POST(req: NextRequest) {
  let domain = "Deployment";
  let difficulty: "easy" | "medium" | "hard" = "medium";

  try {
    const body = (await req.json()) as {
      domain?: string;
      difficulty?: "easy" | "medium" | "hard";
    };
    if (body.domain) domain = body.domain;
    if (body.difficulty) difficulty = body.difficulty;
  } catch {
    // Use defaults if body is absent or malformed
  }

  const { system, user } = buildRexChallengePrompt({ domain, difficulty });

  const result = await callOpenRouterJson<Challenge>({
    model: MODEL,
    systemPrompt: system,
    userMessage: user,
    temperature: 0.8,
    maxTokens: 512,
  });

  if (!result.ok) {
    console.error("[rex/challenge] OpenRouter error:", result.error);
    return NextResponse.json(
      { error: "Failed to generate challenge", details: result.error },
      { status: 502 },
    );
  }

  const challenge = result.data;

  // Validate required fields
  if (
    !challenge.domain ||
    !challenge.topic ||
    !challenge.scenario ||
    !challenge.question
  ) {
    console.error("[rex/challenge] Invalid challenge shape:", challenge);
    return NextResponse.json(
      { error: "Rex returned an invalid challenge shape" },
      { status: 502 },
    );
  }

  // Dev logging per AC 1.3
  if (process.env.NODE_ENV === "development") {
    console.log("[rex/challenge] Generated:", {
      domain: challenge.domain,
      topic: challenge.topic,
    });
  }

  return NextResponse.json(challenge);
}
