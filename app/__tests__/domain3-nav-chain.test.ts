/**
 * AC3 — lesson nav links form a valid chain: 0018→0019→…→0023.
 *
 * Run: npm test -- domain3-nav-chain
 */
import { describe, expect, it } from "vitest";
import { read, findLessonFile } from "./domain3-utils";
import { parseLessonNum } from "./domain3-utils";

// ------------------------------------------------------------------
// Boundary checks
// ------------------------------------------------------------------
describe("AC3 — nav chain boundaries", () => {
  it("0018 next link points to a lesson starting with 0019", () => {
    const f = findLessonFile(18);
    const content = read(f);
    const nextMatch = content.match(/<a href="([^"]+)">Next:/);
    expect(nextMatch, "Could not find Next: nav link in 0018").not.toBeNull();
    const nextNum = parseLessonNum(nextMatch![1]);
    expect(nextNum).toBe(19);
  });

  it("0023 next link is present", () => {
    const f = findLessonFile(23);
    const content = read(f);
    const nextMatch = content.match(/<a href="([^"]+)">Next:/);
    expect(nextMatch).not.toBeNull();
  });
});

// ------------------------------------------------------------------
// Forward chain: each lesson points "next" to its successor
// ------------------------------------------------------------------
describe("AC3 — forward nav chain 0019→0023", () => {
  const chain: readonly (readonly [number, number])[] = [
    [19, 20],
    [20, 21],
    [21, 22],
    [22, 23],
  ];

  for (const [curr, next] of chain) {
    it(`00${curr} next link points to 00${next}`, () => {
      const f = findLessonFile(curr);
      const content = read(f);
      const nextMatch = content.match(/<a href="([^"]+)">Next:/);
      expect(nextMatch).not.toBeNull();
      const nextNum = parseLessonNum(nextMatch![1]);
      expect(nextNum).toBe(next);
    });
  }
});

// ------------------------------------------------------------------
// Backward chain: each lesson points "← Previous" to its predecessor
// ------------------------------------------------------------------
describe("AC3 — backward nav chain 0020←0019 through 0023←0022", () => {
  const chain: readonly (readonly [number, number])[] = [
    [20, 19],
    [21, 20],
    [22, 21],
    [23, 22],
  ];

  for (const [curr, prev] of chain) {
    it(`00${curr} prev link points to 00${prev}`, () => {
      const f = findLessonFile(curr);
      const content = read(f);
      const prevMatch = content.match(/<a href="([^"]+)">← Previous:/);
      expect(prevMatch).not.toBeNull();
      const prevNum = parseLessonNum(prevMatch![1]);
      expect(prevNum).toBe(prev);
    });
  }
});
