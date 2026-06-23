/**
 * Drift coverage for Domain 1–3 curriculum map and quick sheet links.
 *
 * Warns if:
 *  - Curriculum map links to lesson files that don't exist (0001–0023)
 *  - Quick sheet links to lesson files that don't exist
 *  - Any 0001–0023 lesson number referenced in the map actually exists as a file
 *
 * Run: npm test -- domain3-drift
 */
import { describe, expect, it } from "vitest";
import { read, LESSONS_DIR, REFERENCE_DIR, parseLessonNum } from "./domain3-utils";
import { readdirSync } from "fs";
import { extname, join } from "path";
import { ALL_D123_LESSONS } from "./domain3-utils";

// --------------------------------------------------------------------------
// Helpers
// --------------------------------------------------------------------------
function extractFourDigitNums(content: string): number[] {
  const nums = new Set<number>();
  for (const m of content.matchAll(/\b(\d{4})\b/g)) {
    nums.add(parseInt(m[1], 10));
  }
  return [...nums].sort((a, b) => a - b);
}

function hasFileForLesson(num: number): boolean {
  return readdirSync(LESSONS_DIR).some(
    (f) => parseLessonNum(f) === num && extname(f) === ".html"
  );
}

// --------------------------------------------------------------------------
// Curriculum map drift — every referenced 0001–0023 lesson has a file
// --------------------------------------------------------------------------
describe("curriculum map — lesson links are in sync (0001–0023)", () => {
  const mapFile = join(REFERENCE_DIR, "dva-c02-curriculum-map.html");
  const content = read(mapFile);
  const mentionedNums = extractFourDigitNums(content);
  const d123Mentioned = mentionedNums.filter((n) => n >= 1 && n <= 23);

  for (const num of d123Mentioned) {
    it(`curriculum map references 00${num} and the file exists`, () => {
      expect(
        hasFileForLesson(num),
        `curriculum map references 00${num} but no file found`
      ).toBe(true);
    });
  }
});

// --------------------------------------------------------------------------
// Quick sheet drift — every referenced 0001–0023 lesson has a file
// --------------------------------------------------------------------------
describe("quick sheet — lesson links are in sync (0001–0023)", () => {
  const qsFile = join(REFERENCE_DIR, "dva-c02-deployment-quick-sheet.html");
  const content = read(qsFile);
  const mentionedNums = extractFourDigitNums(content);
  const d123Mentioned = mentionedNums.filter((n) => n >= 1 && n <= 23);

  for (const num of d123Mentioned) {
    it(`quick sheet references 00${num} and the file exists`, () => {
      expect(
        hasFileForLesson(num),
        `quick sheet references 00${num} but no file found`
      ).toBe(true);
    });
  }
});

// --------------------------------------------------------------------------
// Curriculum map coverage — every 0001–0023 lesson is mentioned
// --------------------------------------------------------------------------
describe("curriculum map — covers all Domain 1–3 lessons (0001–0023)", () => {
  const mapContent = read(join(REFERENCE_DIR, "dva-c02-curriculum-map.html"));

  for (const num of ALL_D123_LESSONS) {
    it(`curriculum map mentions lesson ${String(num).padStart(4, "0")}`, () => {
      expect(mapContent, `missing 00${num}`).toContain(`00${num}`);
    });
  }
});
