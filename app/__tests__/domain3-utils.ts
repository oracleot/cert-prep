/**
 * Shared helpers for Domain 3 lesson QA tests.
 * Consumed by all domain3-*.test.ts suites.
 */
import { readdirSync, readFileSync } from "fs";
import { extname, join } from "path";

export const LESSONS_DIR = join(process.cwd(), "lessons");
export const REFERENCE_DIR = join(process.cwd(), "reference");
export const MAX_LINES = 200;
export const DOMAIN3_LESSONS = [19, 20, 21, 22, 23] as const;

export function read(path: string): string {
  return readFileSync(path, "utf8");
}

export function countLines(content: string): number {
  return content.split("\n").length;
}

export function parseLessonNum(filename: string): number | null {
  const m = /^(\d{4})/.exec(filename);
  return m ? parseInt(m[1], 10) : null;
}

export function findLessonFile(num: number): string {
  const matches = readdirSync(LESSONS_DIR).filter(
    (f) => parseLessonNum(f) === num && extname(f) === ".html"
  );
  if (matches.length !== 1) {
    throw new Error(`Expected exactly one file for lesson ${num}, got: ${matches.join(", ")}`);
  }
  return join(LESSONS_DIR, matches[0]);
}
