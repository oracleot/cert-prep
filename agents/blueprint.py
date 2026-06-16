from __future__ import annotations

from copy import deepcopy


EXAM_ID = "dva-c02"
EXAM_NAME = "AWS Certified Developer - Associate (DVA-C02)"

_DVA_C02_DOMAINS = [
    {
        "name": "Deployment",
        "weight": 32,
        "topics": [
            "CodeDeploy deployment strategies",
            "Lambda deployment traffic shifting",
            "CI/CD pipelines with CodePipeline",
            "Elastic Beanstalk application deployments",
        ],
    },
    {
        "name": "Security",
        "weight": 26,
        "topics": [
            "IAM least privilege for application code",
            "KMS envelope encryption",
            "Cognito user pools and identity pools",
            "Secrets Manager rotation from applications",
        ],
    },
    {
        "name": "Development",
        "weight": 30,
        "topics": [
            "DynamoDB conditional writes",
            "SQS visibility timeout and retries",
            "API Gateway Lambda proxy integrations",
            "Step Functions error handling",
        ],
    },
    {
        "name": "Troubleshooting",
        "weight": 12,
        "topics": [
            "CloudWatch Logs Insights debugging",
            "X-Ray trace analysis",
            "Lambda concurrency throttling",
            "Dead-letter queues and redrive policies",
        ],
    },
]


def validate_exam_name(exam_name: str) -> tuple[bool, str, str]:
    normalized = " ".join(exam_name.strip().upper().split())
    accepted = normalized in {"DVA-C02", "AWS DVA-C02", EXAM_NAME.upper()}
    return accepted, EXAM_ID, EXAM_NAME


def default_blueprint() -> list[dict]:
    return deepcopy(_DVA_C02_DOMAINS)


def default_curriculum() -> list[dict]:
    domains = default_blueprint()
    for index, domain in enumerate(domains, start=1):
        domain["study_order"] = index
        domain["performance_score"] = 0
    return domains
