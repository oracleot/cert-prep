import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  const backendUrl = process.env.LANGGRAPH_URL || "http://localhost:8000";

  try {
    const body = await req.json();
    const res = await fetch(`${backendUrl}/onboarding/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();

    if (!res.ok || !data.accepted) {
      return NextResponse.json(data, { status: res.ok ? 200 : res.status });
    }

    const { agentQueue } = await import("@/lib/queue");
    await agentQueue.add(
      "blueprint_scout",
      { onboardingId: data.onboarding_id },
      { jobId: `blueprint-${data.onboarding_id}` },
    );

    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "Failed to start onboarding" }, { status: 503 });
  }
}
