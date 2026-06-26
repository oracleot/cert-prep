import { NextRequest, NextResponse } from "next/server";

/**
 * Proxy: POST /api/settings/learning-style
 *
 * Body: { user_id: string, learning_style: string, exam_id?: string }
 * Forwards to agents backend POST /settings/learning-style. The body is
 * passed through verbatim, so an optional `exam_id` (used when the user
 * changes learning style for a non-active curriculum) is forwarded when
 * present. After a successful update the blueprint_scout job is queued
 * for the new onboarding run.
 */

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  const backendUrl = process.env.LANGGRAPH_URL || "http://localhost:8000";

  try {
    const body = await req.json();
    const res = await fetch(`${backendUrl}/settings/learning-style`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();

    if (!res.ok) return NextResponse.json(data, { status: res.status });

    const { agentQueue } = await import("@/lib/queue");
    await agentQueue.add(
      "blueprint_scout",
      { onboardingId: data.onboarding_id },
      { jobId: `settings-blueprint-${data.onboarding_id}` },
    );

    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "Failed to update learning style" }, { status: 503 });
  }
}
