/**
 * Shared helpers for Domain 3 lesson QA tests.
 * Consumed by all domain3-*.test.ts suites.
 */
import { readdirSync, readFileSync } from "fs";
import { extname, join } from "path";

export const LESSONS_DIR = join(process.cwd(), "lessons");
export const REFERENCE_DIR = join(process.cwd(), "reference");
export const MAX_LINES = 200;
/** Domain 1 = 0001-0012, Domain 2 = 0013-0018, Domain 3 = 0019-0023 */
export const DOMAIN_LESSONS = {
  1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] as const,
  2: [13, 14, 15, 16, 17, 18] as const,
  3: [19, 20, 21, 22, 23] as const,
} as const;
export const ALL_D123_LESSONS = [
  ...DOMAIN_LESSONS[1],
  ...DOMAIN_LESSONS[2],
  ...DOMAIN_LESSONS[3],
] as const;

export const LESSON_FILES = readdirSync(LESSONS_DIR).filter(
  (f) => extname(f) === ".html"
);

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
  const matches = LESSON_FILES.filter(
    (f) => parseLessonNum(f) === num && extname(f) === ".html"
  );
  if (matches.length !== 1) {
    throw new Error(`Expected exactly one file for lesson ${num}, got: ${matches.join(", ")}`);
  }
  return join(LESSONS_DIR, matches[0]);
}

// --------------------------------------------------------------------------
// Quiz extraction helpers — shared by walkthrough-schema tests
// --------------------------------------------------------------------------

export function extractQuizBlocks(content: string): string[] {
  const blocks: string[] = [];
  const re = /<section\s+class="quiz"[^>]*data-quiz[^>]*>([\s\S]*?)(?=<section\s+class="quiz"|<nav|$)/g;
  let m;
  while ((m = re.exec(content)) !== null) blocks.push(m[0]);
  return blocks;
}

export function isEnhancedQuiz(block: string): boolean {
  return block.includes('data-walkthrough="true"');
}

export function extractChoices(block: string): string[] {
  return block.match(/<button class="choice"[^>]*>/g) ?? [];
}

export function extractCorrectChoice(block: string): string | null {
  const m = block.match(/<button class="choice"[^>]*data-correct[^>]*>/);
  return m ? m[0] : null;
}

export function extractRationales(block: string): string[] {
  const re = /<aside[^>]*data-rationale-for="([^"]+)"[^>]*>([\s\S]*?)<\/aside>/g;
  const out: string[] = [];
  let m;
  while ((m = re.exec(block)) !== null) out.push(m[0]);
  return out;
}

export function hasExplanation(block: string): boolean {
  return /<aside[^>]*class="[^"]*explanation[^"]*"[^>]*>/.test(block);
}

export function hasKnowledgeGap(block: string): boolean {
  return /<aside[^>]*class="[^"]*knowledge-gap[^"]*"[^>]*>/.test(block);
}

export function hasKeywordCallout(block: string): boolean {
  const stemMatch = block.match(/<section class="quiz"[^>]*>([\s\S]*?)<button/);
  if (!stemMatch) return false;
  return /<(mark|strong)>/.test(stemMatch[1]);
}

export function examLikeStem(block: string): boolean {
  const stemMatch = block.match(/<section class="quiz"[^>]*>([\s\S]*?)<button/);
  if (!stemMatch) return false;
  const plain = stemMatch[1].replace(/<[^>]+>/g, " ").trim();
  const sentences = plain.split(/[.!?]+/).filter((s) => s.trim().length > 0);
  const awsContext = /(aws|amazon|lambda|api[\s-]?gateway|dynamodb|sqs|sns|eventbridge|step[\s-]functions|codebuild|codepipeline|codedeploy|iam|kms|ecs|ec2|cloudformation|sam|cloudwatch|s3|sts|cognito|secrets[\s-]?manager|parameter[\s-]?store)/i.test(plain);
  return sentences.length >= 2 && awsContext;
}

export function hasInternalLessonLinkInGap(block: string): boolean {
  const kg = block.match(/<aside[^>]*class="[^"]*knowledge-gap[^"]*"[^>]*>([\s\S]*?)<\/aside>/);
  if (!kg) return false;
  return /href="(?!https?:\/\/|http:\/\/|#|\/\/)[^"]*\.html"/.test(kg[1]);
}

export function hasAwsDocsLinkInGap(block: string): boolean {
  const kg = block.match(/<aside[^>]*class="[^"]*knowledge-gap[^"]*"[^>]*>([\s\S]*?)<\/aside>/);
  if (!kg) return false;
  return /href="https:\/\/docs\.aws\.amazon\.com/.test(kg[1]);
}

export function gapPromptText(block: string): string | null {
  const kg = block.match(/<aside[^>]*class="[^"]*knowledge-gap[^"]*"[^>]*>([\s\S]*?)<\/aside>/);
  if (!kg) return null;
  const plain = kg[1].replace(/<a[^>]*>([\s\S]*?)<\/a>/g, "$1").replace(/<[^>]+>/g, " ").trim();
  return plain.length > 0 ? plain : null;
}

export function lessonFileForNum(num: number): string | null {
  const matches = LESSON_FILES.filter((f) => parseLessonNum(f) === num);
  return matches.length === 1 ? join(LESSONS_DIR, matches[0]) : null;
}

export function lessonLabel(num: number): string {
  return `lesson ${String(num).padStart(4, "0")}`;
}
