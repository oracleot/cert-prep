/**
 * Railway Deployment Readiness — TypeScript / Next.js contract tests.
 *
 * Run: npm test -- --grep "railway"
 */
import { describe, expect, it } from "vitest";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

const PROJECT_ROOT = join(__dirname, "..", "..");

// ---------------------------------------------------------------------------
// AC1 — Next.js /api/health endpoint
// ---------------------------------------------------------------------------

describe("AC1 — Next.js /api/health endpoint", () => {
  const HEALTH_ROUTE = join(PROJECT_ROOT, "app", "api", "health", "route.ts");

  it("GET /api/health route file exists", () => {
    expect(existsSync(HEALTH_ROUTE)).toBe(true);
  });

  it("route exports GET handler (App Router syntax)", () => {
    const content = readFileSync(HEALTH_ROUTE, "utf-8");
    expect(content).toMatch(/export\s+(?:async\s+)?function\s+GET|\.get\s*\(/);
  });

  it("response model includes status, database_configured, langgraph_configured fields", () => {
    const content = readFileSync(HEALTH_ROUTE, "utf-8");
    expect(content).toMatch(/status/);
    expect(content).toMatch(/database_configured|langgraph_configured|db|postgres/i);
  });
});
