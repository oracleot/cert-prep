"""Shared fixtures for Task 9.6 — Exchange miss-field tests."""
from __future__ import annotations

FAKE_CONCEPT = {
    "id": "deploy-codepipeline-basics",
    "domain": "Deployment",
    "task_statement": "Deploy via CI/CD pipelines.",
    "topic": "CodePipeline Basics",
    "topic_id": "deploy-codepipeline-basics",
    "task_statement_id": "deploy-codepipeline-basics",
    "services": ["CodePipeline", "CodeBuild"],
    "source_ids": ["sb-deploy-pipelines"],
    "familiarity_level": "new",
    "ready": True,
    "facts": [
        "CodePipeline has at least three stages: Source, Build, Deploy.",
        "CodeBuild projects run in isolated build environments.",
    ],
    "traps": [
        "CodeBuild does NOT run inside a VPC by default; "
        "you must explicitly enable VPC mode.",
    ],
    "expected_answer_criteria": (
        "Answer must mention at least one CodePipeline stage type "
        "and note that CodeBuild defaults to no VPC."
    ),
    "official_docs": ["https://docs.aws.amazon.com/codepipeline/latest/userguide/"],
    "skill_builder_links": [],
    "lab_links": [],
}
