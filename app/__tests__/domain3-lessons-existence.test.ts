/**
 * AC1 — Domain 3 lessons 0019–0023 exist, parse, and stay under 200 lines.
 * AC2 — Each lesson has required HTML structure.
 *
 * Run: npm test -- domain3-lessons-existence
 */
import { describe, expect, it } from "vitest";
import { read, countLines, findLessonFile, LESSONS_DIR, MAX_LINES } from "./domain3-utils";
import { readdirSync } from "fs";
import { extname, join } from "path";
import { parseLessonNum } from "./domain3-utils";

describe("AC1 — Domain 3 lessons exist (0019–0023)", () => {
  for (const num of [19, 20, 21, 22, 23] as const) {
    const matching = readdirSync(LESSONS_DIR).filter(
      (f) => parseLessonNum(f) === num && extname(f) === ".html"
    );

    it(`lesson ${num} exists`, () => {
      expect(
        matching.length,
        `Expected exactly one file starting with ${num}, got: ${matching.join(", ")}`
      ).toBe(1);
    });

    it(`lesson ${num} parses as valid HTML`, () => {
      const content = read(join(LESSONS_DIR, matching[0]));
      expect(content).toContain("<!doctype html>");
      expect(content).toContain("<html");
      expect(content).toContain("<main>");
    });

    it(`lesson ${num} is under ${MAX_LINES} lines`, () => {
      const content = read(join(LESSONS_DIR, matching[0]));
      const lines = countLines(content);
      expect(lines, `lesson ${num} has ${lines} lines (max ${MAX_LINES})`).toBeLessThanOrEqual(MAX_LINES);
    });
  }
});

describe("AC2 — required HTML structure in each Domain 3 lesson", () => {
  for (const num of [19, 20, 21, 22, 23] as const) {
    const filename = findLessonFile(num);

    it(`lesson ${num} has kicker, h1, ≥1 quiz, and nav`, () => {
      const content = read(filename);
      expect(content).toContain('<p class="kicker">');
      expect(content).toContain("<h1>");
      expect(content).toContain('data-quiz');
      expect(content).toContain('class="lesson-nav"');
    });

    it(`lesson ${num} has <title> tag`, () => {
      const content = read(filename);
      expect(content).toContain("<title>");
    });
  }
});
