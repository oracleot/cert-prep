/**
 * AC6 — internal lesson and reference links resolve to existing files.
 * Only validates Domain 3 lessons (0018–0023) plus the quick sheet.
 *
 * Run: npm test -- domain3-internal-links
 */
import { describe, expect, it } from "vitest";
import { read, LESSONS_DIR } from "./domain3-utils";
import { existsSync, readdirSync } from "fs";
import { extname, join, resolve } from "path";
import { parseLessonNum } from "./domain3-utils";

describe("AC6 — internal lesson and reference links are resolvable", () => {
  const allLessonFiles = readdirSync(LESSONS_DIR).filter(
    (f) => extname(f) === ".html"
  );

  for (const lessonFile of allLessonFiles) {
    const num = parseLessonNum(lessonFile);
    if (num === null) continue;
    // Only validate Domain 3 lessons and the 0018 boundary
    if (num < 18 || num > 23) continue;

    const content = read(join(LESSONS_DIR, lessonFile));

    // Capture relative hrefs pointing to .html or .md
    const hrefMatches = [...content.matchAll(/href="([^"]*\.(?:html|md))"/g)].map(
      (m) => m[1]
    );

    for (const href of hrefMatches) {
      if (href.startsWith("http") || href.startsWith("//") || href.startsWith("#")) continue;

      it(`${lessonFile} → href="${href}" resolves`, () => {
        const decoded = decodeURIComponent(href);
        const resolved = resolve(LESSONS_DIR, decoded);
        expect(
          existsSync(resolved),
          `href="${href}" (decoded: ${decoded}) from ${lessonFile} does not resolve`
        ).toBe(true);
      });
    }
  }
});
