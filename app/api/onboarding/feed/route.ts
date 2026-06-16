import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const backendUrl = process.env.LANGGRAPH_URL || "http://localhost:8000";
  const onboardingId = req.nextUrl.searchParams.get("onboarding_id");

  if (!onboardingId) {
    return NextResponse.json({ error: "Missing onboarding_id" }, { status: 400 });
  }

  try {
    const res = await fetch(`${backendUrl}/onboarding/${onboardingId}/feed`);
    if (!res.ok) {
      return NextResponse.json({ error: "Backend error" }, { status: res.status });
    }

    return new NextResponse(res.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
      },
    });
  } catch {
    return NextResponse.json({ error: "Failed to connect to backend" }, { status: 503 });
  }
}
