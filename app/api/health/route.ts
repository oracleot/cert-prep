// GET /api/health
// Health check endpoint for Railway deployment verification.
// Returns service status and downstream dependency readiness.

import { type NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const database_configured = Boolean(process.env.DATABASE_URL);
  const langgraph_configured =
    database_configured && Boolean(process.env.LANGGRAPH_URL);

  return NextResponse.json(
    {
      status: "ok",
      database_configured,
      langgraph_configured,
    },
    { status: 200 },
  );
}
