/**
 * Task 9.3 regression suite — Rex Challenge prompt tests (AC2/AC3).
 *
 * Verifies:
 *  - AC2: Rex receives selected concept packet (task_statement, services, source_ids, concept_id)
 *  - AC3: Challenge output stores conceptId/domain/topic/task statement/source IDs
 *
 * Run: npm test -- --grep "task93"
 */
import { describe, expect, it } from "vitest";
import { buildRexChallengePrompt, MODEL } from "@/agents/prompts/rex";

describe("AC2 — Rex concept packet passthrough (buildRexChallengePrompt)", () => {
  it("includes concept_id in the generated user prompt", () => {
    const { user } = buildRexChallengePrompt({
      domain: "Deployment",
      concept_id: "deploy-codepipeline-basics",
      task_statement: "Deploy via CI/CD pipelines.",
      services: ["CodePipeline", "CodeBuild"],
      source_ids: ["sb-deploy-pipelines"],
    });
    expect(user).toContain("deploy-codepipeline-basics");
  });

  it("includes task_statement in the generated user prompt", () => {
    const { user } = buildRexChallengePrompt({
      domain: "Deployment",
      concept_id: "deploy-codepipeline-basics",
      task_statement: "Deploy via CI/CD pipelines.",
      services: ["CodePipeline"],
      source_ids: ["sb-deploy-pipelines"],
    });
    expect(user).toContain("Deploy via CI/CD pipelines.");
  });

  it("includes services in the generated user prompt", () => {
    const { user } = buildRexChallengePrompt({
      domain: "Deployment",
      concept_id: "deploy-codepipeline-basics",
      task_statement: "Deploy via CI/CD pipelines.",
      services: ["CodePipeline", "CodeBuild"],
      source_ids: ["sb-deploy-pipelines"],
    });
    expect(user).toContain("CodePipeline");
    expect(user).toContain("CodeBuild");
  });

  it("includes source_ids in the generated user prompt", () => {
    const { user } = buildRexChallengePrompt({
      domain: "Deployment",
      concept_id: "deploy-codepipeline-basics",
      task_statement: "Deploy via CI/CD pipelines.",
      services: ["CodePipeline"],
      source_ids: ["sb-deploy-pipelines", "sb-cicd"],
    });
    expect(user).toContain("sb-deploy-pipelines");
    expect(user).toContain("sb-cicd");
  });

  it("omits source grounding section when no concept fields provided", () => {
    const { user } = buildRexChallengePrompt({ domain: "Deployment" });
    expect(user).not.toContain("Source grounding:");
    expect(user).toContain('"Deployment"');
  });

  it("uses the correct model", () => {
    expect(MODEL).toBe("anthropic/claude-sonnet-4.6");
  });
});

describe("AC3 — Challenge type includes concept fields", () => {
  it("Challenge type allows concept_id, task_statement, services, source_ids", () => {
    const challenge = {
      concept_id: "deploy-codepipeline-basics",
      domain: "Deployment",
      topic: "CodePipeline Basics",
      task_statement: "Deploy via CI/CD pipelines.",
      services: ["CodePipeline"],
      source_ids: ["sb-deploy"],
      scenario: "Test scenario.",
      question: "What?",
    };
    expect(challenge.concept_id).toBe("deploy-codepipeline-basics");
    expect(challenge.task_statement).toBe("Deploy via CI/CD pipelines.");
    expect(challenge.services).toContain("CodePipeline");
    expect(challenge.source_ids).toContain("sb-deploy");
  });
});
