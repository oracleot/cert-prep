/**
 * Display names for the three exams bundled in V1.
 * See AGENTS.md "Narrow exception: cross-exam curriculum switcher".
 */

export const EXAM_NAMES: Record<string, string> = {
  "dva-c02": "AWS Certified Developer – Associate",
  "saa-c03": "AWS Certified Solutions Architect – Associate",
  "cca-foundations": "AWS Certified Cloud Practitioner – Foundations",
};

export function getExamName(examId: string): string {
  return EXAM_NAMES[examId] ?? examId;
}
