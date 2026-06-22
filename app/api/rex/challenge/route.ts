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
  let task_statement = "";
  let services: string[] = [];
  let source_ids: string[] = [];
  let concept_id = "";

  try {
    const body = (await req.json()) as {
      domain?: string;
      difficulty?: "easy" | "medium" | "hard";
      task_statement?: string;
      services?: string[];
      source_ids?: string[];
      concept_id?: string;
    };
    if (body.domain) domain = body.domain;
    if (body.difficulty) difficulty = body.difficulty;
    if (body.task_statement) task_statement = body.task_statement;
    if (body.services) services = body.services;
    if (body.source_ids) source_ids = body.source_ids;
    if (body.concept_id) concept_id = body.concept_id;
  } catch {
    // Use defaults if body is absent or malformed
  }

  if (!concept_id || !task_statement || source_ids.length === 0) {
    return NextResponse.json(
      { error: "Rex challenge requires a selected concept packet" },
      { status: 422 },
    );
  }

  const { system, user } = buildRexChallengePrompt({
    domain,
    difficulty,
    task_statement,
    services,
    source_ids,
    concept_id,
  });

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

  // Stamp concept fields if provided; they are advisory.
  if (concept_id) challenge.concept_id = concept_id;
  if (task_statement) challenge.task_statement = task_statement;
  if (services.length > 0) challenge.services = services;
  if (source_ids.length > 0) challenge.source_ids = source_ids;

  // Dev logging per AC 1.3
  if (process.env.NODE_ENV === "development") {
    console.log("[rex/challenge] Generated:", {
      domain: challenge.domain,
      topic: challenge.topic,
    });
  }

  return NextResponse.json(challenge);
}
