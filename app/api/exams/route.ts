import { NextResponse } from "next/server";

export async function GET() {
  const backendUrl = process.env.LANGGRAPH_URL || "http://localhost:8000";

  try {
    const res = await fetch(`${backendUrl}/exams`);
    if (!res.ok) {
      return NextResponse.json({ error: "Backend error" }, { status: res.status });
    }
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ error: "Failed to connect to backend" }, { status: 503 });
  }
}
