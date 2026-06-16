from __future__ import annotations

from pathlib import Path
from typing import TypedDict


class Citation(TypedDict):
    url: str
    title: str
    snippet_id: str


class SageGrounding(TypedDict):
    source_context: str
    citations: list[Citation]


SNIPPETS_DIR = Path(__file__).resolve().parent / "data" / "sage_snippets"
EXAM_GUIDE_ROOTS = {
    "dva-c02": "https://docs.aws.amazon.com/aws-certification/latest/developer-associate-02",
    "saa-c03": "https://docs.aws.amazon.com/aws-certification/latest/solutions-architect-associate-03",
}
SERVICE_DOCS = {
    "AWS Lambda": (
        "AWS Lambda developer guide",
        "https://docs.aws.amazon.com/lambda/latest/dg/welcome.html",
        "Lambda runs code without provisioning servers and integrates with event sources such as queues, streams, and API endpoints.",
    ),
    "Amazon API Gateway": (
        "Amazon API Gateway developer guide",
        "https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html",
        "API Gateway creates, publishes, maintains, monitors, and secures APIs for backend services.",
    ),
    "Amazon DynamoDB": (
        "Amazon DynamoDB developer guide",
        "https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html",
        "DynamoDB is a fully managed NoSQL database for key-value and document workloads with single-digit millisecond performance.",
    ),
    "Amazon SQS": (
        "Amazon SQS developer guide",
        "https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html",
        "SQS provides managed message queues for decoupling distributed application components.",
    ),
    "Amazon SNS": (
        "Amazon SNS developer guide",
        "https://docs.aws.amazon.com/sns/latest/dg/welcome.html",
        "SNS is a managed pub/sub messaging service for application-to-application and application-to-person notifications.",
    ),
    "Amazon EventBridge": (
        "Amazon EventBridge user guide",
        "https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html",
        "EventBridge routes events from AWS services, custom applications, and SaaS providers to targets.",
    ),
    "AWS Identity and Access Management (IAM)": (
        "AWS IAM user guide",
        "https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html",
        "IAM controls authentication and authorization for AWS principals, policies, roles, and permissions.",
    ),
    "AWS Step Functions": (
        "AWS Step Functions developer guide",
        "https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html",
        "Step Functions coordinates distributed application components with visual workflows and state machines.",
    ),
}


def load_sage_grounding(
    exam_id: str,
    topic_id: str,
    topic: str,
    services: list[str],
    source_ids: list[str],
) -> SageGrounding:
    file_context, file_citations = _load_snippet_file(exam_id, topic_id)
    if file_citations:
        return {"source_context": file_context, "citations": file_citations}

    citations = _exam_guide_citations(exam_id, source_ids)
    citations.extend(_service_citations(services))
    citations = _dedupe(citations)[:4]

    if not citations:
        return {
            "source_context": "No verified official AWS source was found for this topic.",
            "citations": [],
        }

    lines = [f"Verified AWS sources for {topic} ({topic_id}):"]
    for index, citation in enumerate(citations, start=1):
        snippet = _snippet_for(citation, topic, services)
        lines.append(f"[{index}] {citation['title']}\nURL: {citation['url']}\nSnippet: {snippet}")
    return {"source_context": "\n\n".join(lines), "citations": citations}


def _load_snippet_file(exam_id: str, topic_id: str) -> tuple[str, list[Citation]]:
    path = SNIPPETS_DIR / exam_id / f"{topic_id}.md"
    if not path.exists():
        return "", []

    text = path.read_text(encoding="utf-8")
    citations: list[Citation] = []
    for line in text.splitlines():
        if not line.startswith("Source:"):
            continue
        parts = [part.strip() for part in line.removeprefix("Source:").split("|")]
        if len(parts) == 3 and parts[1].startswith("https://docs.aws.amazon.com/"):
            citations.append({"title": parts[0], "url": parts[1], "snippet_id": parts[2]})
    return text, citations


def _exam_guide_citations(exam_id: str, source_ids: list[str]) -> list[Citation]:
    root = EXAM_GUIDE_ROOTS.get(exam_id)
    if not root:
        return []

    citations: list[Citation] = []
    for source_id in source_ids:
        page, _, fragment = source_id.partition("#")
        if not page.endswith(".md"):
            continue
        html_page = page.removesuffix(".md") + ".html"
        url = f"{root}/{html_page}"
        if fragment:
            url = f"{url}#{fragment}"
        title = f"AWS exam guide: {page.removesuffix('.md')}"
        citations.append({"url": url, "title": title, "snippet_id": source_id})
    return citations


def _service_citations(services: list[str]) -> list[Citation]:
    citations: list[Citation] = []
    for service in services:
        doc = SERVICE_DOCS.get(service)
        if not doc:
            continue
        title, url, _ = doc
        citations.append({"url": url, "title": title, "snippet_id": f"aws-service-docs:{service}"})
    return citations


def _dedupe(citations: list[Citation]) -> list[Citation]:
    seen: set[str] = set()
    unique: list[Citation] = []
    for citation in citations:
        if citation["url"] in seen:
            continue
        seen.add(citation["url"])
        unique.append(citation)
    return unique


def _snippet_for(citation: Citation, topic: str, services: list[str]) -> str:
    for service in services:
        doc = SERVICE_DOCS.get(service)
        if doc and doc[1] == citation["url"]:
            return doc[2]
    service_text = ", ".join(services) if services else "the listed AWS services"
    return f"Official exam guide context for {topic}, including {service_text}."
