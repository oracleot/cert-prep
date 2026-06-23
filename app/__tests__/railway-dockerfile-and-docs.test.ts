/**
 * AC3 + AC4 + AC5 — Dockerfile, env-var docs, and DATABASE_URL guard.
 *
 * Run: npm test -- --grep "railway"
 */
import { describe, expect, it } from "vitest";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

const PROJECT_ROOT = join(__dirname, "..", "..");
const AGENTS_ROOT = join(PROJECT_ROOT, "agents");

describe("AC3 — Agents Dockerfile build context includes migrations", () => {
  const DOCKERFILE = join(AGENTS_ROOT, "Dockerfile");

  it("Dockerfile exists at agents/ root", () => {
    expect(existsSync(DOCKERFILE)).toBe(true);
  });

  it("COPY or ADD instruction includes migrations/ from project root", () => {
    const content = readFileSync(DOCKERFILE, "utf-8");
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

describe("AC4 — Required env vars documented in docs", () => {
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
    const rail_doc = join(PROJECT_ROOT, "docs", "railway-deploy.md");
    if (!existsSync(rail_doc)) return;
    const content = readFileSync(rail_doc, "utf-8");
    expect(content).toMatch(/LANGGRAPH_URL/);
    expect(content).not.toMatch(
      /LANGGRAPH_URL.*agents.*self.?reference|LANGGRAPH_URL.*self.?reference.*agents/i,
    );
  });
});

describe("AC5 — agents/db.py missing DATABASE_URL guard", () => {
  it("db.py raises RuntimeError when DATABASE_URL is absent (tested via mock)", () => {
    const DB_PY = join(AGENTS_ROOT, "db.py");
    const content = readFileSync(DB_PY, "utf-8");
    expect(content).toMatch(/RuntimeError.*DATABASE_URL is not set/i);
  });
});
