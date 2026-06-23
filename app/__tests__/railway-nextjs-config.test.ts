/**
 * AC2 + AC6 — Next.js railway.toml config + no invalid multi-service config.
 *
 * Run: npm test -- --grep "railway"
 */
import { describe, expect, it } from "vitest";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

const RA_ROOT = join(__dirname, "..", "..");

describe("AC2 — Next.js railway.toml", () => {
  const NEXT_RAILWAY = join(RA_ROOT, "railway.toml");

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

  it("uses Railway schema buildCommand (not snake_case)", () => {
    const content = readFileSync(NEXT_RAILWAY, "utf-8");
    expect(content).toMatch(/buildCommand/);
    expect(content).not.toMatch(/build_command/);
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
    expect(content).not.toMatch(/agents|python|fastapi|uvicorn/);
  });
});

describe("AC6 — No invalid single multi-service Railway config", () => {
  it("root railway.toml does not declare both nextjs and agents services", () => {
    const ROOT_RAILWAY = join(RA_ROOT, "railway.toml");
    if (!existsSync(ROOT_RAILWAY)) return;
    const content = readFileSync(ROOT_RAILWAY, "utf-8");
    const has_nextjs = /nextjs|web|frontend/.test(content);
    const has_agents = /agents|python|fastapi|uvicorn/.test(content);
    expect(has_nextjs && has_agents).toBe(false);
  });
});
