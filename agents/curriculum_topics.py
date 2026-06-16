from __future__ import annotations

from typing import Any


def topic_label(topic: Any) -> str:
    if isinstance(topic, dict):
        return str(topic.get("name") or topic.get("id") or "")
    return str(topic)


def topic_key(topic: Any) -> str:
    if isinstance(topic, dict):
        return str(topic.get("id") or topic.get("name") or "")
    return str(topic)


def topic_payload(topic: Any) -> dict[str, Any]:
    if isinstance(topic, dict):
        return {**topic, "name": topic_label(topic)}
    return {"id": topic, "name": str(topic), "services": [], "source_ids": []}


def coverage_matrix(domains: list[dict], topic_stats: dict[str, dict[str, int]]) -> list[dict]:
    matrix = []
    for domain in domains:
        topics = []
        for topic in domain.get("topics", []):
            name = topic_label(topic)
            stat = topic_stats.get(name, {"correct_count": 0, "total_count": 0})
            total = stat["total_count"]
            status = "covered" if stat["correct_count"] else "in_progress" if total else "untouched"
            topics.append({
                **topic_payload(topic),
                "status": status,
                "correct_count": stat["correct_count"],
                "total_count": total,
            })
        matrix.append({**domain, "topics": topics})
    return matrix


def valid_domains(value: Any, blueprint: list[dict] | None = None) -> bool:
    if not isinstance(value, list) or not all(
        isinstance(item, dict)
        and {"name", "weight", "topics", "study_order"}.issubset(item)
        for item in value
    ):
        return False
    if not blueprint:
        return True

    expected = {domain["name"]: domain for domain in blueprint}
    if {domain["name"] for domain in value} != set(expected):
        return False
    for domain in value:
        source = expected[domain["name"]]
        if domain.get("weight") != source.get("weight"):
            return False
        if topic_keys(domain.get("topics", [])) != topic_keys(source.get("topics", [])):
            return False
        if source.get("task_statements") and domain.get("task_statements") != source.get("task_statements"):
            return False
    return True


def topic_keys(topics: list[Any]) -> set[str]:
    return {topic_key(topic) for topic in topics}
