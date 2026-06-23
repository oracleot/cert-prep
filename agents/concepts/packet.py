"""Runtime concept packet normalization for task 9.3."""
from __future__ import annotations

from typing import Any

_PREFIXES = ("deploy-", "dev-", "sec-", "trouble-")
_TOKEN_LABELS = {
    "api": "API",
    "cicd": "CI/CD",
    "codepipeline": "CodePipeline",
    "dynamodb": "DynamoDB",
    "iam": "IAM",
    "kms": "KMS",
    "lambda": "Lambda",
}
_SERVICE_HINTS = {
    "api gateway": "API Gateway",
    "cloudformation": "CloudFormation",
    "cloudwatch": "CloudWatch",
    "codebuild": "CodeBuild",
    "codedeploy": "CodeDeploy",
    "codepipeline": "CodePipeline",
    "dynamodb": "DynamoDB",
    "eventbridge": "EventBridge",
    "iam": "IAM",
    "kms": "KMS",
    "lambda": "Lambda",
    "s3": "S3",
    "secrets manager": "Secrets Manager",
    "sns": "SNS",
    "sqs": "SQS",
    "x-ray": "X-Ray",
}


def concept_topic(record: dict[str, Any]) -> str:
    """Return a stable human label even when YAML only has an id."""
    explicit = str(record.get("topic", "")).strip()
    if explicit:
        return explicit
    concept_id = str(record.get("id", "")).strip()
    for prefix in _PREFIXES:
        if concept_id.startswith(prefix):
            concept_id = concept_id[len(prefix):]
            break
    return " ".join(_TOKEN_LABELS.get(part, part.title()) for part in concept_id.split("-"))


def concept_source_ids(record: dict[str, Any]) -> list[str]:
    existing = record.get("source_ids")
    if isinstance(existing, list) and existing:
        return [str(item) for item in existing if str(item).strip()]
    lesson = str(record.get("lesson_reference", "")).strip()
    return [lesson] if lesson else []


def concept_services(record: dict[str, Any]) -> list[str]:
    existing = record.get("services")
    if isinstance(existing, list) and existing:
        return [str(item) for item in existing if str(item).strip()]
    haystack = " ".join(
        [
            str(record.get("id", "")),
            str(record.get("task_statement", "")),
            " ".join(map(str, record.get("facts", []))),
            " ".join(map(str, record.get("traps", []))),
            " ".join(map(str, record.get("official_docs", []))),
        ]
    ).lower()
    services: list[str] = []
    for needle, label in _SERVICE_HINTS.items():
        if needle in haystack and label not in services:
            services.append(label)
    return services


def concept_packet_fields(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize optional runtime fields from the curated concept record.

    Phase 9.4 / 9.5 — the packet now also carries the curated facts / traps /
    expected-answer-criteria and the link lists (official docs, Skill Builder,
    hands-on labs). These are forwarded to Rex, the Evaluator, and Sage so
    each agent is grounded to the packet rather than free-responding.
    """
    concept_id = str(record.get("id", ""))
    return {
        "topic": concept_topic(record),
        "topic_id": str(record.get("topic_id") or concept_id),
        "task_statement_id": str(record.get("task_statement_id") or concept_id),
        "services": concept_services(record),
        "source_ids": concept_source_ids(record),
        "difficulty": str(record.get("difficulty") or "medium"),
        "familiarity_level": str(record.get("familiarity_level") or "new"),
        "facts": list(record.get("facts") or []),
        "traps": list(record.get("traps") or []),
        "expected_answer_criteria": str(record.get("expected_answer_criteria") or ""),
        "official_docs": list(record.get("official_docs") or []),
        "skill_builder_links": list(record.get("skill_builder_links") or []),
        "lab_links": list(record.get("lab_links") or []),
    }
