import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const backendUrl = process.env.LANGGRAPH_URL || "http://localhost:8000";

  try {
    const body = await req.json();
    const res = await fetch(`${backendUrl}/history/list`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      return NextResponse.json({ error: "Backend error" }, { status: res.status });
    }

    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ error: "Failed to connect to backend" }, { status: 503 });
  }
}
