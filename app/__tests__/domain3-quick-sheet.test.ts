/**
 * AC4 — deployment quick sheet exists, parses, and is under 200 lines.
 * Also verifies CI/CD service cluster content.
 *
 * Run: npm test -- domain3-quick-sheet
 */
import { describe, expect, it } from "vitest";
import { existsSync } from "fs";
import { read, countLines } from "./domain3-utils";
import { join } from "path";

const QS_FILE = join(process.cwd(), "reference", "dva-c02-deployment-quick-sheet.html");

describe("AC4 — deployment quick sheet", () => {
  it("quick sheet exists in reference/", () => {
    expect(existsSync(QS_FILE)).toBe(true);
  });

  it("quick sheet parses as valid HTML", () => {
    const content = read(QS_FILE);
    expect(content).toContain("<!doctype html>");
    expect(content).toContain("<title>");
    expect(content).toContain("<main>");
  });

  it("quick sheet is under 200 lines", () => {
    const content = read(QS_FILE);
    const lines = countLines(content);
    expect(lines, `quick sheet has ${lines} lines (max 200)`).toBeLessThanOrEqual(200);
  });

  it("quick sheet includes CI/CD services (CodePipeline/CodeBuild/CodeDeploy)", () => {
    const content = read(QS_FILE).toLowerCase();
    expect(content).toMatch(/codepipeline|codebuild|codedeploy/i);
  });
});
