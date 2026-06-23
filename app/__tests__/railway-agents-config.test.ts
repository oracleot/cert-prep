/**
 * AC2 — Agents railway.toml config.
 *
 * Run: npm test -- --grep "railway"
 */
import { describe, expect, it } from "vitest";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

const PROJECT_ROOT = join(__dirname, "..", "..");
const AGENTS_ROOT = join(PROJECT_ROOT, "agents");

describe("AC2 — Agents railway.toml", () => {
  const AGENTS_RAILWAY = join(AGENTS_ROOT, "railway.toml");

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

  it("uses Railway schema dockerfilePath (not snake_case)", () => {
    const content = readFileSync(AGENTS_RAILWAY, "utf-8");
    expect(content).toMatch(/dockerfilePath/);
    expect(content).not.toMatch(/dockerfile_path/);
  });

  it("documents python/fastapi as the service", () => {
    const content = readFileSync(AGENTS_RAILWAY, "utf-8");
    expect(content).toMatch(/python|fastapi|uvicorn/);
  });
});
