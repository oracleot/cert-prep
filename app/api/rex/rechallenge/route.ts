// POST /api/rex/rechallenge
// Returns a harder Rex challenge after Sage has responded.
// Expects: { domain, previousTopic, difficulty, task_statement?, services?, source_ids?, concept_id? }

import { type NextRequest, NextResponse } from "next/server";
import { callOpenRouterJson } from "@/lib/openrouter-json";
import { buildRexRechallengePrompt, MODEL } from "@/agents/prompts/rex";
import type { Challenge } from "@/lib/types";

export async function POST(req: NextRequest) {
  let domain = "Deployment";
  let previousTopic = "";
  let difficulty: "easy" | "medium" | "hard" = "hard";
  let task_statement = "";
  let services: string[] = [];
  let source_ids: string[] = [];
  let concept_id = "";

  try {
    const body = (await req.json()) as {
      domain?: string;
      previousTopic?: string;
      difficulty?: "easy" | "medium" | "hard";
      task_statement?: string;
      services?: string[];
      source_ids?: string[];
      concept_id?: string;
    };
    if (body.domain) domain = body.domain;
    if (body.previousTopic) previousTopic = body.previousTopic;
    if (body.difficulty) difficulty = body.difficulty;
    if (body.task_statement) task_statement = body.task_statement;
    if (body.services) services = body.services;
    if (body.source_ids) source_ids = body.source_ids;
    if (body.concept_id) concept_id = body.concept_id;
  } catch {
    // Use defaults
  }

  const { system, user } = buildRexRechallengePrompt({
    domain,
    previousTopic,
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
    console.error("[rex/rechallenge] Invalid rechallenge shape:", challenge);
    return NextResponse.json(
      { error: "Rex returned an invalid rechallenge shape" },
      { status: 502 },
    );
  }

  // Stamp concept fields if provided; they are advisory.
  if (concept_id) challenge.concept_id = concept_id;
  if (task_statement) challenge.task_statement = task_statement;
  if (services.length > 0) challenge.services = services;
  if (source_ids.length > 0) challenge.source_ids = source_ids;

  if (process.env.NODE_ENV === "development") {
    console.log("[rex/rechallenge] Generated harder challenge:", {
      domain: challenge.domain,
      topic: challenge.topic,
    });
  }

  return NextResponse.json(challenge);
}
