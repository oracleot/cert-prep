import { NextRequest, NextResponse } from "next/server";

/**
 * Proxy: POST /api/settings/reset-progress
 *
 * Body: { user_id: string, exam_id: string }
 * Forwards to agents backend POST /settings/reset-progress. `exam_id` is
 * now required by the backend; the proxy simply forwards whatever the
 * client sends, and 400/422 errors from the backend propagate as-is.
 */

export async function POST(req: NextRequest) {
  const backendUrl = process.env.LANGGRAPH_URL || "http://localhost:8000";

  try {
    const body = await req.json();
    const res = await fetch(`${backendUrl}/settings/reset-progress`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: "Failed to reset progress" }, { status: 503 });
  }
}
