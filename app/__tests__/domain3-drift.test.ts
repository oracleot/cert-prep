/**
 * Drift coverage for Domain 3 quick sheet and curriculum map links.
 *
 * Warns if:
 *  - Curriculum map links to lesson files that don't exist
 *  - Quick sheet links to lesson files that don't exist
 *  - Curriculum map claims Domain 3 but lesson files are missing
 *
 * These links can silently drift out of sync when content is moved or renamed.
 *
 * Run: npm test -- domain3-drift
 */
import { describe, expect, it } from "vitest";
import { read, LESSONS_DIR, REFERENCE_DIR } from "./domain3-utils";
import { readdirSync } from "fs";
import { extname, join } from "path";
import { parseLessonNum } from "./domain3-utils";

// ------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------
function extractLessonNumbersFromContent(content: string): number[] {
  const nums = new Set<number>();
  const matches = content.matchAll(/\b(\d{4})\b/g);
  for (const m of matches) {
    nums.add(parseInt(m[1], 10));
  }
  return [...nums].sort((a, b) => a - b);
}

function hasFileForLesson(num: number): boolean {
  return readdirSync(LESSONS_DIR).some(
    (f) => parseLessonNum(f) === num && extname(f) === ".html"
  );
}

// ------------------------------------------------------------------
// Curriculum map drift
// ------------------------------------------------------------------
describe("curriculum map — lesson links are in sync", () => {
  const mapFile = join(REFERENCE_DIR, "dva-c02-curriculum-map.html");
  const content = read(mapFile);
  // Domain 3 lessons are 0019–0023; check all that appear in the map exist
  const mentionedNums = extractLessonNumbersFromContent(content);
  const d3Mentioned = mentionedNums.filter((n) => n >= 19 && n <= 23);

  for (const num of d3Mentioned) {
    it(`curriculum map mentions 00${num} and the file exists`, () => {
      expect(hasFileForLesson(num), `curriculum map references 00${num} but no file found`).toBe(
        true
      );
    });
  }
});

// ------------------------------------------------------------------
// Quick sheet drift
// ------------------------------------------------------------------
describe("quick sheet — lesson links are in sync", () => {
  const qsFile = join(REFERENCE_DIR, "dva-c02-deployment-quick-sheet.html");
  const content = read(qsFile);
  const mentionedNums = extractLessonNumbersFromContent(content);
  const d3Mentioned = mentionedNums.filter((n) => n >= 19 && n <= 23);

  for (const num of d3Mentioned) {
    it(`quick sheet mentions 00${num} and the file exists`, () => {
      expect(hasFileForLesson(num), `quick sheet references 00${num} but no file found`).toBe(
        true
      );
    });
  }
});

// ------------------------------------------------------------------
// Lesson → curriculum map coverage
// Ensures every Domain 3 lesson number is mentioned in the curriculum map
// ------------------------------------------------------------------
describe("curriculum map — covers all Domain 3 lessons", () => {
  const mapContent = read(join(REFERENCE_DIR, "dva-c02-curriculum-map.html"));

  for (const num of [19, 20, 21, 22, 23] as const) {
    it(`curriculum map mentions lesson 00${num}`, () => {
      expect(mapContent).toContain(`00${num}`);
    });
  }
});
