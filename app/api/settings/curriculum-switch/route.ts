import { NextRequest, NextResponse } from "next/server";

/**
 * Proxy: POST /api/settings/curriculum-switch
 *
 * Body: { user_id: string, exam_id: string }
 * Forwards to agents backend POST /settings/curriculum-switch.
 *
 * Backend response shapes:
 *   200 { status: "ready", curriculum_id, exam_id, exam_name }
 *   200 { status: "needs_onboarding", exam_id, exam_name, redirect_to }
 *   400 unsupported exam_id
 *   503 backend unavailable
 * The 200/200 split is intentional — the client decides whether to
 * route to /onboarding or resume /session based on `status`.
 */

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  const backendUrl = process.env.LANGGRAPH_URL || "http://localhost:8000";

  try {
    const body = await req.json();
    const res = await fetch(`${backendUrl}/settings/curriculum-switch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: "Failed to switch curriculum" }, { status: 503 });
  }
}