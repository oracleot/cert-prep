/**
 * Domain 3 lesson creation QA contract (Goal Lock: DVA-C02 Domain 3 lessons).
 *
 * Verifies:
 *  - AC1: lessons 0019–0023 exist, parse, and are under 200 lines each
 *  - AC2: each lesson has required HTML structure (doctype, kicker, h1, ≥1 quiz, nav)
 *  - AC3: lesson nav links form a valid chain: 0018→0019→…→0023
 *  - AC4: reference/dva-c02-deployment-quick-sheet.html exists, parses, ≤200 lines
 *  - AC5: reference/dva-c02-curriculum-map.html updated to include Domain 3 lesson links
 *  - AC6: lesson internal links to other lessons resolve to files that exist
 *
 * Run: npm test -- domain3
 */
import { describe, expect, it } from "vitest";
import { readFileSync, existsSync, readdirSync } from "fs";
import { join, resolve, extname } from "path";

const LESSONS_DIR = join(process.cwd(), "lessons");
const REFERENCE_DIR = join(process.cwd(), "reference");
const MAX_LINES = 200;

function read(path: string): string {
  return readFileSync(path, "utf8");
}

function countLines(content: string): number {
  return content.split("\n").length;
}

function parseLessonNum(filename: string): number | null {
  const m = /^(\d{4})/.exec(filename);
  return m ? parseInt(m[1], 10) : null;
}

// ------------------------------------------------------------------
// AC1 — all five lessons exist and parse as valid HTML
// ------------------------------------------------------------------
const LESSON_FILES = [
  "0019",
  "0020",
  "0021",
  "0022",
  "0023",
];

describe("AC1 — Domain 3 lessons exist (0019–0023)", () => {
  for (const num of LESSON_FILES) {
    const matching = readdirSync(LESSONS_DIR).filter(
      (f) => parseLessonNum(f) === parseInt(num, 10) && extname(f) === ".html"
    );

    it(`lesson ${num} exists`, () => {
      expect(matching.length, `Expected exactly one file starting with ${num}, got: ${matching.join(", ")}`).toBe(1);
      expect(existsSync(join(LESSONS_DIR, matching[0]))).toBe(true);
    });

    it(`lesson ${num} parses without throwing`, () => {
      const content = read(join(LESSONS_DIR, matching[0]));
      expect(() => {
        const doc = content; // basic string parse — full DOM parse not needed in node env
        expect(doc).toContain("<!doctype html>");
        expect(doc).toContain("<html");
        expect(doc).toContain("<main>");
      }).not.toThrow();
    });

    it(`lesson ${num} is under ${MAX_LINES} lines`, () => {
      const content = read(join(LESSONS_DIR, matching[0]));
      const lines = countLines(content);
      expect(lines, `lesson ${num} has ${lines} lines (max ${MAX_LINES})`).toBeLessThanOrEqual(MAX_LINES);
    });
  }
});

// ------------------------------------------------------------------
// AC2 — each lesson has required structural elements
// ------------------------------------------------------------------
describe("AC2 — required HTML structure in each Domain 3 lesson", () => {
  for (const num of LESSON_FILES) {
    const matching = readdirSync(LESSONS_DIR).filter(
      (f) => parseLessonNum(f) === parseInt(num, 10) && extname(f) === ".html"
    );

    it(`lesson ${num} has kicker, h1, ≥1 quiz, and nav`, () => {
      const content = read(join(LESSONS_DIR, matching[0]));
      expect(content).toContain('<p class="kicker">');
      expect(content).toContain("<h1>");
      expect(content).toContain('data-quiz');
      expect(content).toContain('class="lesson-nav"');
    });

    it(`lesson ${num} has title tag`, () => {
      const content = read(join(LESSONS_DIR, matching[0]));
      expect(content).toContain("<title>");
    });
  }
});

// ------------------------------------------------------------------
// AC3 — nav chain: 0018→0019→…→0023
// ------------------------------------------------------------------
describe("AC3 — lesson nav chain integrity", () => {
  // 0018 is the last Domain 2 lesson; its "next" should point to 0019
  it("0018 next link points to a lesson starting with 0019", () => {
    const f = readdirSync(LESSONS_DIR).filter(
      (f) => parseLessonNum(f) === 18 && extname(f) === ".html"
    );
    expect(f.length).toBe(1);
    const content = read(join(LESSONS_DIR, f[0]));
    // extract next nav link href
    const nextMatch = content.match(/<a href="([^"]+)">Next:/);
    expect(nextMatch, "Could not find Next: nav link in 0018").not.toBeNull();
    const nextHref = nextMatch![1]; // e.g. "0019-*.html"
    const nextNum = parseLessonNum(nextHref);
    expect(nextNum).toBe(19);
  });

  // 0023 is the last Domain 3 lesson; its "next" should point to a Domain 4 lesson or reference
  it("0023 next link is present", () => {
    const f = readdirSync(LESSONS_DIR).filter(
      (f) => parseLessonNum(f) === 23 && extname(f) === ".html"
    );
    expect(f.length).toBe(1);
    const content = read(join(LESSONS_DIR, f[0]));
    const nextMatch = content.match(/<a href="([^"]+)">Next:/);
    expect(nextMatch).not.toBeNull();
  });

  // Each consecutive pair 0019→0020→0021→0022→0023 must chain
  const chain = [19, 20, 21, 22, 23];
  for (let i = 0; i < chain.length - 1; i++) {
    const curr = chain[i];
    const next = chain[i + 1];
    it(`00${curr} next link points to 00${next}`, () => {
      const f = readdirSync(LESSONS_DIR).filter(
        (f) => parseLessonNum(f) === curr && extname(f) === ".html"
      );
      const content = read(join(LESSONS_DIR, f[0]));
      const nextMatch = content.match(/<a href="([^"]+)">Next:/);
      expect(nextMatch).not.toBeNull();
      const nextNum = parseLessonNum(nextMatch![1]);
      expect(nextNum).toBe(next);
    });
  }

  // Each lesson's "previous" link points to the correct predecessor
  for (let i = 1; i < chain.length; i++) {
    const curr = chain[i];
    const prev = chain[i - 1];
    it(`00${curr} prev link points to 00${prev}`, () => {
      const f = readdirSync(LESSONS_DIR).filter(
        (f) => parseLessonNum(f) === curr && extname(f) === ".html"
      );
      const content = read(join(LESSONS_DIR, f[0]));
      const prevMatch = content.match(/<a href="([^"]+)">← Previous:/);
      expect(prevMatch).not.toBeNull();
      const prevNum = parseLessonNum(prevMatch![1]);
      expect(prevNum).toBe(prev);
    });
  }
});

// ------------------------------------------------------------------
// AC4 — deployment quick sheet
// ------------------------------------------------------------------
describe("AC4 — deployment quick sheet", () => {
  const QS_FILE = "dva-c02-deployment-quick-sheet.html";

  it("deployment quick sheet exists", () => {
    expect(existsSync(join(REFERENCE_DIR, QS_FILE))).toBe(true);
  });

  it("deployment quick sheet parses", () => {
    const content = read(join(REFERENCE_DIR, QS_FILE));
    expect(content).toContain("<!doctype html>");
    expect(content).toContain("<title>");
    expect(content).toContain("<main>");
  });

  it("deployment quick sheet is under 200 lines", () => {
    const content = read(join(REFERENCE_DIR, QS_FILE));
    const lines = countLines(content);
    expect(lines, `quick sheet has ${lines} lines (max ${MAX_LINES})`).toBeLessThanOrEqual(MAX_LINES);
  });

  it("deployment quick sheet includes CI/CD services (CodePipeline/CodeBuild/CodeDeploy)", () => {
    const content = read(join(REFERENCE_DIR, QS_FILE)).toLowerCase();
    expect(content).toMatch(/codepipeline|codebuild|codedeploy/i);
  });
});

// ------------------------------------------------------------------
// AC5 — curriculum map updated for Domain 3
// ------------------------------------------------------------------
describe("AC5 — curriculum map includes Domain 3 lessons", () => {
  const MAP_FILE = join(REFERENCE_DIR, "dva-c02-curriculum-map.html");
  const content = read(MAP_FILE);

  it("curriculum map mentions Domain 3 task statements", () => {
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

// ------------------------------------------------------------------
// AC6 — internal lesson links resolve to existing files
// ------------------------------------------------------------------
describe("AC6 — internal lesson and reference links are resolvable", () => {
  const allLessonFiles = readdirSync(LESSONS_DIR).filter(
    (f) => extname(f) === ".html"
  );

  for (const lessonFile of allLessonFiles) {
    const num = parseLessonNum(lessonFile);
    if (num === null) continue;
    // Only validate Domain 3 lessons (and 0018 boundary)
    if (num < 18 || num > 23) continue;

    const content = read(join(LESSONS_DIR, lessonFile));

    // Match href values that look like relative lesson or reference links
    const hrefMatches = [...content.matchAll(/href="([^"]*\.(?:html|md))"/g)].map(
      (m) => m[1]
    );

    for (const href of hrefMatches) {
      if (href.startsWith("http") || href.startsWith("//")) continue;
      if (href.startsWith("#")) continue;

      it(`${lessonFile} → href="${href}" resolves`, () => {
        // Decode URL-encoded chars (e.g. %20 → space) and resolve relative to LESSONS_DIR
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
