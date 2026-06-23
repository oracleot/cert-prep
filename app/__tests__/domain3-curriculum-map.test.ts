/**
 * AC5 — curriculum map updated to include Domain 3 lesson links and
 * CI/CD service cluster.
 *
 * Run: npm test -- domain3-curriculum-map
 */
import { describe, expect, it } from "vitest";
import { read } from "./domain3-utils";
import { join } from "path";

const MAP_FILE = join(process.cwd(), "reference", "dva-c02-curriculum-map.html");

describe("AC5 — curriculum map includes Domain 3 lessons", () => {
  const content = read(MAP_FILE);

  it("curriculum map mentions Domain 3 Deployment task statements", () => {
    expect(content).toMatch(/Domain 3.*Deployment/i);
  });

  it("curriculum map includes lesson 0019 link", () => {
    expect(content).toContain("0019");
  });

  it("curriculum map includes lesson 0023 link", () => {
    expect(content).toContain("0023");
  });

  it("curriculum map includes deployment quick sheet link", () => {
    expect(content).toContain("deployment-quick-sheet");
  });

  it("curriculum map includes CI/CD service cluster keywords", () => {
    const lower = content.toLowerCase();
    expect(lower).toMatch(/codepipeline|codebuild|codedeploy/i);
  });
});
