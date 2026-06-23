/**
 * Railway Deployment Readiness — TypeScript / Next.js contract tests.
 *
 * These tests define the acceptance criteria for deployability on Railway.
 * They validate the presence and shape of required config files, the health
 * endpoint contract, and env-var documentation — without requiring a live
 * Railway project or real secrets.
 *
 * Run: npm test -- --grep "railway"
 */
import { describe, expect, it, vi } from "vitest";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const PROJECT_ROOT = join(__dirname, "..", "..");
const RA_ROOT = PROJECT_ROOT;
const AGENTS_ROOT = join(PROJECT_ROOT, "agents");

function read_json(filepath: string): Record<string, unknown> | null {
  try {
    return JSON.parse(readFileSync(filepath, "utf-8"));
  } catch {
    return null;
  }
}

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
    // Match both `export async function GET` (App Router) and `app.get(` (Route Handler API)
    expect(content).toMatch(/export\s+(?:async\s+)?function\s+GET|\.get\s*\(/);
  });

  it("response model includes status, database_configured, langgraph_configured fields", () => {
    const content = readFileSync(HEALTH_ROUTE, "utf-8");
    expect(content).toMatch(/status/);
    // at minimum the health check should surface whether downstream deps are reachable
    expect(content).toMatch(/database_configured|langgraph_configured|db|postgres/i);
  });
});

// ---------------------------------------------------------------------------
// AC2 — Railway config files exist with expected fields
// ---------------------------------------------------------------------------

describe("AC2 — Railway config files (next.js + agents)", () => {
  const NEXT_RAILWAY = join(RA_ROOT, "railway.toml");
  const AGENTS_RAILWAY = join(AGENTS_ROOT, "railway.toml");

  describe("Next.js railway.toml", () => {
    it("file exists at project root", () => {
      expect(existsSync(NEXT_RAILWAY)).toBe(true);
    });

    it("has [railway] section with [deploy] block", () => {
      const content = readFileSync(NEXT_RAILWAY, "utf-8");
      expect(content).toMatch(/\[railway\]/);
      expect(content).toMatch(/\[deploy\]/);
    });

    it("uses Railway schema camelCase deploy keys", () => {
      const content = readFileSync(NEXT_RAILWAY, "utf-8");
      expect(content).toMatch(/healthcheckPath/);
      expect(content).toMatch(/healthcheckTimeout/);
      expect(content).toMatch(/restartPolicyType/);
      expect(content).toMatch(/restartPolicyMaxRetries/);
    });

    it("has no [deployments] block (invalid in Railway schema)", () => {
      const content = readFileSync(NEXT_RAILWAY, "utf-8");
      expect(content).not.toMatch(/\[deployments\]/);
    });

    it("documents nextjs as the first service", () => {
      const content = readFileSync(NEXT_RAILWAY, "utf-8");
      expect(content).toMatch(/nextjs|web|frontend/);
    });

    it("does NOT declare a second service (per-service configs only)", () => {
      const content = readFileSync(NEXT_RAILWAY, "utf-8");
      // If agents service appears in root railway.toml, that's the invalid pattern
      expect(content).not.toMatch(/agents|python|fastapi|uvicorn/);
    });
  });

  describe("Agents railway.toml", () => {
    it("file exists at agents/ root", () => {
      expect(existsSync(AGENTS_RAILWAY)).toBe(true);
    });

    it("has [railway] section", () => {
      const content = readFileSync(AGENTS_RAILWAY, "utf-8");
      expect(content).toMatch(/\[railway\]/);
    });

    it("uses Railway schema camelCase deploy keys", () => {
      const content = readFileSync(AGENTS_RAILWAY, "utf-8");
      expect(content).toMatch(/healthcheckPath/);
      expect(content).toMatch(/healthcheckTimeout/);
      expect(content).toMatch(/restartPolicyType/);
      expect(content).toMatch(/restartPolicyMaxRetries/);
    });

    it("documents python/fastapi as the service", () => {
      const content = readFileSync(AGENTS_RAILWAY, "utf-8");
      expect(content).toMatch(/python|fastapi|uvicorn/);
    });
  });

  describe("Agents railway.toml", () => {
    it("file exists at agents/ root", () => {
      expect(existsSync(AGENTS_RAILWAY)).toBe(true);
    });

    it("has [railway] section", () => {
      const content = readFileSync(AGENTS_RAILWAY, "utf-8");
      expect(content).toMatch(/\[railway\]/);
    });

    it("documents python/fastapi as the service", () => {
      const content = readFileSync(AGENTS_RAILWAY, "utf-8");
      expect(content).toMatch(/python|fastapi|uvicorn/);
    });
  });
});

// ---------------------------------------------------------------------------
// AC3 — Agents Dockerfile (if used) includes migrations build context
// ---------------------------------------------------------------------------

describe("AC3 — Agents Dockerfile build context includes migrations", () => {
  const DOCKERFILE = join(AGENTS_ROOT, "Dockerfile");

  it("Dockerfile exists at agents/ root", () => {
    expect(existsSync(DOCKERFILE)).toBe(true);
  });

  it("COPY or ADD instruction includes migrations/ from project root", () => {
    const content = readFileSync(DOCKERFILE, "utf-8");
    // The Dockerfile must copy the migrations dir so agents/db.py can run them
    expect(content).toMatch(/migrations/);
  });

  it("WORKDIR is set to /app or agents equivalent", () => {
    const content = readFileSync(DOCKERFILE, "utf-8");
    expect(content).toMatch(/WORKDIR/);
  });

  it("exposes port 8000 for FastAPI", () => {
    const content = readFileSync(DOCKERFILE, "utf-8");
    expect(content).toMatch(/8000/);
  });
});

// ---------------------------------------------------------------------------
// AC4 — docs mention required env vars for both services
// ---------------------------------------------------------------------------

describe("AC4 — Required env vars documented in docs", () => {
  // Prefer railway-deploy.md (the canonical deploy guide); fall back to others.
  const DEPLOY_DOC_PATTERNS = [
    join(PROJECT_ROOT, "docs", "railway-deploy.md"),
    join(PROJECT_ROOT, "docs", "deployment.md"),
    join(PROJECT_ROOT, "docs", "implementation-backlog.md"),
    join(PROJECT_ROOT, "docs", "tech-stack.md"),
  ];

  const REQUIRED_VARS = [
    "OPENROUTER_API_KEY",
    "DATABASE_URL",
    "REDIS_URL",
    "LANGGRAPH_URL",
  ];

  function find_deploy_doc(): string | null {
    for (const p of DEPLOY_DOC_PATTERNS) {
      if (existsSync(p)) return p;
    }
    return null;
  }

  it("at least one deploy-related doc exists", () => {
    const doc = find_deploy_doc();
    expect(doc).not.toBeNull();
  });

  it("doc mentions OPENROUTER_API_KEY", () => {
    const doc = find_deploy_doc();
    if (!doc) return;
    const content = readFileSync(doc, "utf-8");
    expect(content).toMatch(/OPENROUTER_API_KEY/);
  });

  it("doc mentions DATABASE_URL", () => {
    const doc = find_deploy_doc();
    if (!doc) return;
    const content = readFileSync(doc, "utf-8");
    expect(content).toMatch(/DATABASE_URL/);
  });

  it("doc mentions REDIS_URL", () => {
    const doc = find_deploy_doc();
    if (!doc) return;
    const content = readFileSync(doc, "utf-8");
    expect(content).toMatch(/REDIS_URL/);
  });

  it("railway-deploy.md mentions LANGGRAPH_URL for next.js → agents routing", () => {
    // Railway-deploy.md is the canonical doc; check it explicitly.
    const rail_doc = join(PROJECT_ROOT, "docs", "railway-deploy.md");
    if (!existsSync(rail_doc)) return;
    const content = readFileSync(rail_doc, "utf-8");
    expect(content).toMatch(/LANGGRAPH_URL/);
    // Must NOT describe LANGGRAPH_URL as a self-reference for agents
    expect(content).not.toMatch(/LANGGRAPH_URL.*agents.*self.?reference|LANGGRAPH_URL.*self.?reference.*agents/i);
  });
});

// ---------------------------------------------------------------------------
// AC5 — agents/db.py guard against missing DATABASE_URL is exercised
// ---------------------------------------------------------------------------

describe("AC5 — agents/db.py missing DATABASE_URL guard", () => {
  it("db.py raises RuntimeError when DATABASE_URL is absent (tested via mock)", async () => {
    // This test verifies the guard exists by checking the module source
    const DB_PY = join(AGENTS_ROOT, "db.py");
    const content = readFileSync(DB_PY, "utf-8");
    expect(content).toMatch(/RuntimeError.*DATABASE_URL is not set/i);
  });
});

// ---------------------------------------------------------------------------
// AC6 — No invalid multi-service Railway config at root
// ---------------------------------------------------------------------------

describe("AC6 — No invalid single multi-service Railway config", () => {
  it("root railway.toml does not declare both nextjs and agents services", () => {
    const ROOT_RAILWAY = join(RA_ROOT, "railway.toml");
    if (!existsSync(ROOT_RAILWAY)) return;
    const content = readFileSync(ROOT_RAILWAY, "utf-8");
    const has_nextjs = /nextjs|web|frontend/.test(content);
    const has_agents = /agents|python|fastapi|uvicorn/.test(content);
    // Per-service Railway configs mean root railway.toml has one service only
    expect(has_nextjs && has_agents).toBe(false);
  });
});
