import { NextRequest, NextResponse } from "next/server";

/**
 * Proxy: POST /api/settings/curricula
 *
 * Body: { user_id: string }
 * Forwards to agents backend POST /settings/curricula, which returns
 * `{ curricula: [{ curriculum_id, exam_id, exam_name, learning_style,
 * active, created_at }, ...] }`. Errors propagate as-is so the UI can
 * distinguish 4xx (bad request) from 503 (backend unavailable).
 */

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  const backendUrl = process.env.LANGGRAPH_URL || "http://localhost:8000";

  try {
    const body = await req.json();
    const res = await fetch(`${backendUrl}/settings/curricula`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: "Failed to list curricula" }, { status: 503 });
  }
}