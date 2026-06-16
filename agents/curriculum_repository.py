from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from blueprint import default_curriculum
from db import get_pool, has_pool
from llm import get_llm
from prompts.curriculum_builder import MODEL, build_curriculum_prompt


def _strip_code_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\n?|```$", "", text, flags=re.MULTILINE).strip()


def _fallback_curriculum(learning_style: str) -> list[dict]:
    domains = default_curriculum()
    if learning_style == "pressure_drills":
        order = ["Development", "Deployment", "Security", "Troubleshooting"]
    elif learning_style == "guided_explanations":
        order = ["Security", "Development", "Deployment", "Troubleshooting"]
    else:
        order = ["Deployment", "Development", "Security", "Troubleshooting"]
    rank = {name: index for index, name in enumerate(order, start=1)}
    for domain in domains:
        domain["study_order"] = rank.get(domain["name"], 99)
    return sorted(domains, key=lambda item: item["study_order"])


def build_curriculum(blueprint: list[dict], learning_style: str) -> list[dict]:
    try:
        system, user = build_curriculum_prompt(blueprint, learning_style)
        response = get_llm(MODEL).invoke([SystemMessage(content=system), HumanMessage(content=user)])
        raw = response.content if isinstance(response.content, str) else str(response.content)
        domains = json.loads(_strip_code_fences(raw))
        if _valid_domains(domains):
            return sorted(domains, key=lambda item: item["study_order"])
    except Exception:
        pass
    return _fallback_curriculum(learning_style)


async def create_curriculum(
    user_id: str,
    exam_id: str,
    onboarding_id: str,
    domains: list[dict],
) -> str:
    if not has_pool():
        return ""

    pool = get_pool()
    async with pool.connection() as conn:
        await conn.execute(
            "UPDATE curricula SET active = FALSE WHERE user_id = %s AND exam_id = %s",
            (user_id, exam_id),
        )
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO curricula (user_id, exam_id, onboarding_run_id, domains, active) "
                "VALUES (%s, %s, %s, %s, TRUE) RETURNING id",
                (user_id, exam_id, onboarding_id, json.dumps(domains)),
            )
            row = await cur.fetchone()
        await conn.commit()
    return str(row[0])


async def get_active_curriculum(user_id: str, exam_id: str) -> dict[str, Any] | None:
    if not has_pool():
        return None

    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id, domains FROM curricula WHERE user_id = %s AND exam_id = %s "
                "AND active = TRUE ORDER BY created_at DESC LIMIT 1",
                (user_id, exam_id),
            )
            row = await cur.fetchone()
    if not row:
        return None
    return {"id": str(row[0]), "domains": _coerce_domains(row[1])}


async def choose_today_target(user_id: str, exam_id: str) -> dict[str, str]:
    curriculum = await get_active_curriculum(user_id, exam_id)
    domains = curriculum["domains"] if curriculum else default_curriculum()
    stats = await _performance_map(user_id, exam_id)

    def score(domain: dict) -> tuple[int, int]:
        stat = stats.get(domain["name"], {"total_count": 0})
        return stat["total_count"], domain.get("study_order", 99)

    selected = sorted(domains, key=score)[0]
    total = stats.get(selected["name"], {"total_count": 0})["total_count"]
    topics = selected.get("topics") or [selected["name"]]
    return {
        "curriculum_id": curriculum["id"] if curriculum else "",
        "domain": selected["name"],
        "topic": topics[total % len(topics)],
    }


async def dashboard_summary(user_id: str, exam_id: str) -> dict[str, Any]:
    curriculum = await get_active_curriculum(user_id, exam_id)
    domains = curriculum["domains"] if curriculum else default_curriculum()
    stats = await _performance_map(user_id, exam_id)
    overview = _domain_overview(domains, stats)
    correct = sum(item["correct_count"] for item in stats.values())
    total = sum(item["total_count"] for item in stats.values())
    readiness = round(sum(item["weight"] * item["performance_score"] for item in overview))
    today = await choose_today_target(user_id, exam_id)
    return {
        "readiness_score": readiness,
        "today_domain": today["domain"],
        "today_topic": today["topic"],
        "rex_record": {"user_wins": correct, "rex_wins": total - correct},
        "domains": overview,
    }


async def progress_map(user_id: str, exam_id: str) -> dict[str, Any]:
    summary = await dashboard_summary(user_id, exam_id)
    return {"domains": summary["domains"]}


async def _performance_map(user_id: str, exam_id: str) -> dict[str, dict[str, int]]:
    if not has_pool():
        return {}
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT domain, correct_count, total_count FROM performance_aggregates "
                "WHERE user_id = %s AND exam_id = %s",
                (user_id, exam_id),
            )
            rows = await cur.fetchall()
    return {row[0]: {"correct_count": row[1], "total_count": row[2]} for row in rows}


def _domain_overview(domains: list[dict], stats: dict[str, dict[str, int]]) -> list[dict]:
    overview = []
    for domain in sorted(domains, key=lambda item: item.get("study_order", 99)):
        stat = stats.get(domain["name"], {"correct_count": 0, "total_count": 0})
        total = stat["total_count"]
        topic_count = max(len(domain.get("topics", [])), 1)
        performance = stat["correct_count"] / total if total else 0
        overview.append({
            **domain,
            "correct_count": stat["correct_count"],
            "total_count": total,
            "performance_score": round(performance, 2),
            "completion_percent": min(100, round((total / (topic_count * 2)) * 100)),
        })
    return overview


def _coerce_domains(value: Any) -> list[dict]:
    return json.loads(value) if isinstance(value, str) else value


def _valid_domains(value: Any) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, dict)
        and {"name", "weight", "topics", "study_order"}.issubset(item)
        for item in value
    )
