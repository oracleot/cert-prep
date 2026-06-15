import { NextResponse } from "next/server";

export async function POST() {
  const backendUrl = process.env.LANGGRAPH_URL || "http://localhost:8000";
  try {
    const res = await fetch(`${backendUrl}/session/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: "dev-user" }),
    });

    if (!res.ok) {
      return NextResponse.json({ error: "Backend error" }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "Failed to connect to backend" }, { status: 503 });
  }
}
