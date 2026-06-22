/**
 * Task 9.3 regression suite — Rex Rechallenge prompt tests (AC2/AC4).
 *
 * Verifies:
 *  - AC2: Rex receives concept packet for rechallenge
 *  - AC4: Rechallenge uses app-selected weak/uncovered/related concept; no free-roam
 *
 * Run: npm test -- --grep "task93"
 */
import { describe, expect, it } from "vitest";
import { buildRexRechallengePrompt } from "@/agents/prompts/rex";

describe("AC2 / AC4 — Rex rechallenge concept packet passthrough", () => {
  it("includes concept_id in the rechallenge user prompt", () => {
    const { user } = buildRexRechallengePrompt({
      domain: "Deployment",
      previousTopic: "CodePipeline Basics",
      concept_id: "deploy-cicd-services",
      task_statement: "Use CI/CD services.",
      services: ["CodePipeline", "CodeBuild", "CodeDeploy"],
      source_ids: ["sb-cicd"],
    });
    expect(user).toContain("deploy-cicd-services");
  });

  it("includes task_statement in the rechallenge user prompt", () => {
    const { user } = buildRexRechallengePrompt({
      domain: "Deployment",
      previousTopic: "CodePipeline Basics",
      concept_id: "deploy-cicd-services",
      task_statement: "Use CI/CD services: CodePipeline, CodeBuild, CodeDeploy.",
      services: ["CodePipeline", "CodeBuild", "CodeDeploy"],
      source_ids: ["sb-cicd"],
    });
    expect(user).toContain("Use CI/CD services:");
  });

  it("includes services in the rechallenge user prompt", () => {
    const { user } = buildRexRechallengePrompt({
      domain: "Deployment",
      previousTopic: "CodePipeline Basics",
      concept_id: "deploy-cicd-services",
      task_statement: "Use CI/CD services.",
      services: ["CodePipeline", "CodeBuild", "CodeDeploy"],
      source_ids: ["sb-cicd"],
    });
    expect(user).toContain("CodePipeline");
    expect(user).toContain("CodeDeploy");
  });

  it("includes source_ids in the rechallenge user prompt", () => {
    const { user } = buildRexRechallengePrompt({
      domain: "Deployment",
      previousTopic: "CodePipeline Basics",
      concept_id: "deploy-cicd-services",
      task_statement: "Use CI/CD services.",
      services: ["CodePipeline"],
      source_ids: ["sb-cicd"],
    });
    expect(user).toContain("sb-cicd");
  });

  it("includes previousTopic in the rechallenge user prompt", () => {
    const { user } = buildRexRechallengePrompt({
      domain: "Deployment",
      previousTopic: "CodePipeline Basics",
      concept_id: "deploy-cicd-services",
    });
    expect(user).toContain("CodePipeline Basics");
  });

  it("includes difficulty override in rechallenge prompt", () => {
    const { user } = buildRexRechallengePrompt({
      domain: "Deployment",
      previousTopic: "CodePipeline Basics",
      concept_id: "deploy-cicd-services",
      task_statement: "Use CI/CD services.",
      services: ["CodePipeline"],
      source_ids: [],
      difficulty: "hard",
    });
    expect(user).toContain("hard");
  });
});

describe("AC4 — Rechallenge prompt constrains domain, no free-roam", () => {
  it("hardcodes SAME domain constraint in rechallenge prompt", () => {
    const { user } = buildRexRechallengePrompt({
      domain: "Security",
      previousTopic: "IAM Authentication",
      concept_id: "sec-iam-authentication",
    });
    expect(user).toContain("SAME domain");
    expect(user).toContain("Security");
  });

  it("mentions raising the stakes / different topic in rechallenge", () => {
    const { user } = buildRexRechallengePrompt({
      domain: "Deployment",
      previousTopic: "CodePipeline Basics",
      concept_id: "deploy-cicd-services",
    });
    expect(user).toContain("different topic");
    expect(user).toContain("harder");
  });
});
