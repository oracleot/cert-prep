/**
 * Schema validation for enhanced walkthrough-format quizzes across all
 * Domain 1–3 lessons (0001–0023).
 *
 * Each enhanced quiz must carry data-walkthrough="true" and contain:
 *   - Exam-like scenario stem (≥ 1 sentence, AWS service context)
 *   - Keyword/requirement callouts (marked with <mark> or <strong>)
 *   - Four <button class="choice"> elements
 *   - One <button class="choice" data-correct>
 *   - Rationale <aside data-rationale-for="A|B|C|D"> for each choice
 *   - <aside class="explanation"> explaining the correct answer
 *   - <aside class="knowledge-gap"> with a gap-identification prompt
 *   - ≥1 internal lesson link in the knowledge-gap section
 *   - ≥1 AWS docs link (href starting with https://docs.aws.amazon.com)
 *
 * Run: npm test -- domain-walkthrough-schema
 */
import { describe, expect, it } from "vitest";
import {
  read,
  countLines,
  LESSON_FILES,
  LESSONS_DIR,
  MAX_LINES,
  ALL_D123_LESSONS,
  extractQuizBlocks,
  isEnhancedQuiz,
  extractChoices,
  extractCorrectChoice,
  extractRationales,
  hasExplanation,
  hasKnowledgeGap,
  hasKeywordCallout,
  examLikeStem,
  hasInternalLessonLinkInGap,
  hasAwsDocsLinkInGap,
  gapPromptText,
} from "./domain3-utils";
import { join } from "path";

// --------------------------------------------------------------------------
// AC: lesson inventory (0001–0023)
// --------------------------------------------------------------------------
describe("lesson inventory — domains 1–3 (0001–0023)", () => {
  for (const num of ALL_D123_LESSONS) {
    const matching = LESSON_FILES.filter(
      (f) => parseInt(f.slice(0, 4)) === num
    );
    it(`lesson ${String(num).padStart(4, "0")} exists`, () => {
      expect(
        matching.length,
        `Expected exactly one file for ${num}, got: ${matching.join(", ")}`
      ).toBe(1);
    });
  }
});

// --------------------------------------------------------------------------
// AC: file-level line cap (0001–0023)
// --------------------------------------------------------------------------
describe("file-level checks — lessons 0001–0023 under 200 lines", () => {
  for (const num of ALL_D123_LESSONS) {
    const matching = LESSON_FILES.filter(
      (f) => parseInt(f.slice(0, 4)) === num
    );
    if (matching.length !== 1) continue;

    it(`lesson ${String(num).padStart(4, "0")} ≤ ${MAX_LINES} lines`, () => {
      const content = read(join(LESSONS_DIR, matching[0]));
      const lines = countLines(content);
      expect(
        lines,
        `lesson ${String(num).padStart(4, "0")} has ${lines} lines`
      ).toBeLessThanOrEqual(MAX_LINES);
    });
  }
});

// --------------------------------------------------------------------------
// AC: quiz presence (0001–0023)
// --------------------------------------------------------------------------
describe("quiz presence — lessons 0001–0023 have ≥1 quiz block", () => {
  for (const num of ALL_D123_LESSONS) {
    const matching = LESSON_FILES.filter(
      (f) => parseInt(f.slice(0, 4)) === num
    );
    if (matching.length !== 1) continue;

    it(`lesson ${String(num).padStart(4, "0")} has ≥1 quiz block`, () => {
      const content = read(join(LESSONS_DIR, matching[0]));
      const blocks = extractQuizBlocks(content);
      expect(
        blocks.length,
        `lesson ${String(num).padStart(4, "0")} has ${blocks.length} quiz blocks`
      ).toBeGreaterThanOrEqual(1);
    });
  }
});

// --------------------------------------------------------------------------
// AC: enhanced walkthrough format (0001–0023)
// --------------------------------------------------------------------------
describe("enhanced walkthrough format — lessons 0001–0023", () => {
  for (const num of ALL_D123_LESSONS) {
    const matching = LESSON_FILES.filter(
      (f) => parseInt(f.slice(0, 4)) === num
    );
    if (matching.length !== 1) continue;

    const content = read(join(LESSONS_DIR, matching[0]));
    const blocks = extractQuizBlocks(content);
    const label = `lesson ${String(num).padStart(4, "0")}`;

    if (blocks.length === 0) {
      it(`${label} has quiz blocks`, () => {
        expect(blocks.length).toBeGreaterThan(0);
      });
      continue;
    }

    for (let i = 0; i < blocks.length; i++) {
      const block = blocks[i];
      const q = `${label} quiz[${i + 1}]`;

      it(`${q} is marked data-walkthrough="true"`, () => {
        expect(
          block.includes('data-walkthrough="true"'),
          `${q}: missing data-walkthrough="true"`
        ).toBe(true);
      });

      if (!isEnhancedQuiz(block)) continue;

      it(`${q} has exactly 4 choices`, () => {
        const choices = extractChoices(block);
        expect(choices.length, `${q}: got ${choices.length} choices`).toBe(4);
      });

      it(`${q} marks one correct answer with data-correct`, () => {
        expect(extractCorrectChoice(block), `${q}: missing data-correct`).not.toBeNull();
      });

      it(`${q} has ≥3 rationale <aside> elements`, () => {
        const rationales = extractRationales(block);
        expect(
          rationales.length,
          `${q}: got ${rationales.length} rationales`
        ).toBeGreaterThanOrEqual(3);
      });

      it(`${q} has <aside class="explanation">`, () => {
        expect(hasExplanation(block), `${q}: missing explanation`).toBe(true);
      });

      it(`${q} has <aside class="knowledge-gap">`, () => {
        expect(hasKnowledgeGap(block), `${q}: missing knowledge-gap`).toBe(true);
      });

      it(`${q} stem has keyword callouts (<mark> or <strong>)`, () => {
        expect(hasKeywordCallout(block), `${q}: no keyword callout`).toBe(true);
      });

      it(`${q} stem reads as exam-like (≥2 sentences + AWS context)`, () => {
        expect(examLikeStem(block), `${q}: stem not exam-like`).toBe(true);
      });

      it(`${q} knowledge-gap has ≥1 internal .html lesson link`, () => {
        expect(
          hasInternalLessonLinkInGap(block),
          `${q}: no internal lesson link in gap`
        ).toBe(true);
      });

      it(`${q} knowledge-gap has ≥1 AWS docs link`, () => {
        expect(
          hasAwsDocsLinkInGap(block),
          `${q}: no docs.aws.amazon.com link in gap`
        ).toBe(true);
      });

      it(`${q} knowledge-gap has non-empty prompt text`, () => {
        expect(gapPromptText(block), `${q}: gap appears empty`).not.toBeNull();
      });
    }
  }
});
