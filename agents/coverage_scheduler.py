from __future__ import annotations

from typing import Any

from curriculum_topics import topic_label, topic_payload


def select_today_target(
    domains: list[dict],
    domain_stats: dict[str, dict[str, int]],
    topic_stats: dict[str, dict[str, int]],
    curriculum_id: str = "",
    domain_difficulties: dict[str, str] | None = None,
    focus_domain: str = "",
) -> dict[str, Any]:
    candidates = _focus_candidates(domains, topic_stats, focus_domain)
    if not candidates:
        candidates = _candidates(domains, topic_stats)
    if not candidates:
        return _empty_target(curriculum_id)

    total_attempts = sum(stat.get("total_count", 0) for stat in domain_stats.values())
    selected = min(
        candidates,
        key=lambda item: _coverage_key(item, domain_stats, total_attempts),
    )
    return _target_payload(selected, curriculum_id, domain_difficulties or {})


def _focus_candidates(domains: list[dict], topic_stats: dict[str, dict[str, int]], focus_domain: str) -> list[dict[str, Any]]:
    candidates = _candidates(domains, topic_stats)
    normalized = focus_domain.strip().casefold()
    if not normalized:
        return candidates
    focused = [item for item in candidates if item["domain"].strip().casefold() == normalized]
    return focused or candidates


def select_rechallenge_target(
    domains: list[dict],
    domain: str,
    previous_topic: str,
    previous_task_statement_id: str,
    topic_stats: dict[str, dict[str, int]],
    curriculum_id: str = "",
) -> dict[str, Any]:
    candidates = [
        item for item in _candidates(domains, topic_stats)
        if item["domain"] == domain and item["topic"]["name"] != previous_topic
    ]
    if not candidates:
        candidates = [item for item in _candidates(domains, topic_stats) if item["domain"] == domain]
    if not candidates:
        return _empty_target(curriculum_id)

    same_task = [
        item for item in candidates
        if item["topic"].get("task_statement_id") == previous_task_statement_id
    ]
    pool = _weak_or_uncovered(same_task) or _weak_or_uncovered(candidates) or same_task or candidates
    selected = min(pool, key=lambda item: (_topic_rank(item), item["stat"]["total_count"], item["topic"]["name"]))
    target = _target_payload(selected, curriculum_id, {})
    return {**target, "difficulty": "hard"}


def _candidates(domains: list[dict], topic_stats: dict[str, dict[str, int]]) -> list[dict[str, Any]]:
    rows = []
    for domain in domains:
        task_map = {
            task.get("id"): task.get("text", "")
            for task in domain.get("task_statements", [])
            if isinstance(task, dict)
        }
        for raw_topic in domain.get("topics", []) or [domain.get("name", "")]:
            topic = topic_payload(raw_topic)
            name = topic_label(topic)
            rows.append({
                "domain": domain.get("name", ""),
                "domain_weight": domain.get("weight", 0),
                "study_order": domain.get("study_order", 99),
                "topic": topic,
                "task_statement": task_map.get(topic.get("task_statement_id"), ""),
                "stat": _stat(topic_stats, name),
            })
    return rows


def _coverage_key(item: dict, domain_stats: dict[str, dict[str, int]], total_attempts: int) -> tuple:
    domain_total = domain_stats.get(item["domain"], {}).get("total_count", 0)
    expected = total_attempts * (item["domain_weight"] / 100)
    return (
        _topic_rank(item),
        domain_total - expected,
        item["stat"]["total_count"],
        -item["domain_weight"],
        item["study_order"],
        item["topic"]["name"],
    )


def _topic_rank(item: dict) -> int:
    stat = item["stat"]
    total = stat["total_count"]
    correct = stat["correct_count"]
    if total == 0:
        return 0
    if correct < total:
        return 1
    return 2


def _difficulty(domain: str, domain_difficulties: dict[str, str]) -> str:
    difficulty = domain_difficulties.get(domain, "easy")
    return difficulty if difficulty in {"easy", "medium", "hard"} else "easy"


def _stat(topic_stats: dict[str, dict[str, int]], topic: str) -> dict[str, int]:
    stat = topic_stats.get(topic, {})
    return {
        "correct_count": stat.get("correct_count", 0),
        "total_count": stat.get("total_count", 0),
    }


def _weak_or_uncovered(candidates: list[dict]) -> list[dict]:
    return [item for item in candidates if _topic_rank(item) < 2]


def _target_payload(item: dict, curriculum_id: str, domain_difficulties: dict[str, str]) -> dict[str, Any]:
    topic = item["topic"]
    return {
        "curriculum_id": curriculum_id,
        "domain": item["domain"],
        "topic": topic["name"],
        "topic_id": topic.get("id", ""),
        "task_statement_id": topic.get("task_statement_id", ""),
        "task_statement": item["task_statement"],
        "services": topic.get("services", []),
        "source_ids": topic.get("source_ids", []),
        "difficulty": _difficulty(item["domain"], domain_difficulties),
    }


def _empty_target(curriculum_id: str) -> dict[str, Any]:
    return {
        "curriculum_id": curriculum_id,
        "domain": "",
        "topic": "",
        "topic_id": "",
        "task_statement_id": "",
        "task_statement": "",
        "services": [],
        "source_ids": [],
        "difficulty": "medium",
    }
