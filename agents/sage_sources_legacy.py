"""Legacy Sage grounding helpers (Phase 9.5 boundary).

Pre-9.5, ``sage_sources.load_sage_grounding`` built a citation list by combining
exam-guide page URLs and a hand-curated ``SERVICE_DOCS`` map. Phase 9.5 grounds
Sage exclusively to the active concept packet
(``official_docs`` / ``skill_builder_links`` / ``lab_links``) and forbids any
service-name fallback that could mint URLs the curator never approved.

This module keeps the legacy snippet/exam-guide/service helpers so
``evals/content_quality.py`` and any older caller can still import them; the
9.5 packet-only path in ``sage_sources.load_sage_grounding`` never invokes them.
"""
from __future__ import annotations

from pathlib import Path
from typing import TypedDict


class Citation(TypedDict):
    url: str
    title: str
    snippet_id: str


SNIPPETS_DIR = Path(__file__).resolve().parent / "data" / "sage_snippets"
EXAM_GUIDE_ROOTS = {
    "dva-c02": "https://docs.aws.amazon.com/aws-certification/latest/developer-associate-02",
    "saa-c03": "https://docs.aws.amazon.com/aws-certification/latest/solutions-architect-associate-03",
    "cca-foundations": "https://claudecertifications.com/claude-certified-architect",
}
SERVICE_DOCS = {
    "Claude Agent SDK": (
        "Claude Code overview",
        "https://docs.anthropic.com/en/docs/claude-code/overview",
        "Claude Code supports custom agents and the Agent SDK for controlled orchestration across tools and sessions.",
    ),
    "Claude Code": (
        "Claude Code overview",
        "https://docs.anthropic.com/en/docs/claude-code/overview",
        "Claude Code is an agentic coding tool that reads codebases, edits files, runs commands, and integrates with development workflows.",
    ),
    "Claude Code CLI": (
        "Claude Code overview",
        "https://docs.anthropic.com/en/docs/claude-code/overview",
        "Claude Code can be scripted from the CLI for development automation, reviews, and CI-style workflows.",
    ),
    "Model Context Protocol (MCP)": (
        "Model Context Protocol introduction",
        "https://modelcontextprotocol.io/introduction",
        "MCP standardizes how AI applications connect to external tools, data sources, and workflows.",
    ),
    "Tool use": (
        "Tool use with Claude",
        "https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview",
        "Tool use lets Claude request structured calls, return stop_reason tool_use, and receive tool_result content from the application.",
    ),
    "Messages API": (
        "Anthropic Messages API",
        "https://docs.anthropic.com/en/api/messages",
        "The Messages API uses structured message content and exposes controls such as tools, system prompts, and output configuration.",
    ),
    "Prompt engineering": (
        "Prompt engineering overview",
        "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview",
        "Prompt engineering starts with success criteria and evaluations, then uses explicit instructions and examples to improve reliability.",
    ),
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
        if len(parts) == 3 and _is_verified_url(parts[1]):
            citations.append({"title": parts[0], "url": parts[1], "snippet_id": parts[2]})
    return text, citations


def _exam_guide_citations(exam_id: str, source_ids: list[str]) -> list[Citation]:
    root = EXAM_GUIDE_ROOTS.get(exam_id)
    if not root:
        return []

    citations: list[Citation] = []
    for source_id in source_ids:
        page, _, fragment = source_id.partition("#")
        if page.startswith("https://"):
            url = f"{page}#{fragment}" if fragment else page
            citations.append({"url": url, "title": f"Exam guide source: {fragment or page}", "snippet_id": source_id})
            continue
        if not page.endswith(".md"):
            continue
        html_page = page.removesuffix(".md") + ".html"
        url = f"{root}/{html_page}"
        if fragment:
            url = f"{url}#{fragment}"
        title = f"Exam guide: {page.removesuffix('.md')}"
        citations.append({"url": url, "title": title, "snippet_id": source_id})
    return citations


def _service_citations(services: list[str]) -> list[Citation]:
    citations: list[Citation] = []
    for service in services:
        doc = SERVICE_DOCS.get(service)
        if not doc:
            continue
        title, url, _ = doc
        citations.append({"url": url, "title": title, "snippet_id": f"reference-docs:{service}"})
    return citations


def _is_verified_url(url: str) -> bool:
    return url.startswith(("https://docs.aws.amazon.com/", "https://docs.anthropic.com/", "https://modelcontextprotocol.io/"))


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
    service_text = ", ".join(services) if services else "the listed services or concepts"
    return f"Official exam guide context for {topic}, including {service_text}."
