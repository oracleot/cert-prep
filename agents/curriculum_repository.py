from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from blueprint import default_curriculum
from curriculum_progress import domain_overview, performance_map, topic_performance_map
from coverage_scheduler import select_rechallenge_target, select_today_target
from curriculum_topics import coverage_matrix, valid_domains
from db import get_pool, has_pool
from exam_artifacts.loader import load_artifact_from_file
from llm import get_llm
from performance_repository import calculate_readiness, read_readiness_score, read_rex_record
from streak_repository import read_session_streak
from prompts.curriculum_builder import MODEL, build_curriculum_prompt


def _strip_code_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?\n?|```$", "", text, flags=re.MULTILINE).strip()


def _fallback_curriculum(blueprint: list[dict], learning_style: str) -> list[dict]:
    domains = deepcopy(blueprint) if blueprint else default_curriculum()
    if learning_style == "pressure_drills":
        order = ["development", "deployment", "security", "troubleshooting"]
    elif learning_style == "guided_explanations":
        order = ["security", "development", "deployment", "troubleshooting"]
    else:
        order = ["deployment", "development", "security", "troubleshooting"]

    def rank_for(name: str) -> int:
        lower = name.lower()
        for index, token in enumerate(order, start=1):
            if token in lower:
                return index
        return 99

    for domain in domains:
        domain["study_order"] = rank_for(domain["name"])
        domain.setdefault("performance_score", 0)
    return sorted(domains, key=lambda item: item["study_order"])


def build_curriculum(blueprint: list[dict], learning_style: str) -> list[dict]:
    try:
        system, user = build_curriculum_prompt(blueprint, learning_style)
        response = get_llm(MODEL).invoke([SystemMessage(content=system), HumanMessage(content=user)])
        raw = response.content if isinstance(response.content, str) else str(response.content)
        domains = json.loads(_strip_code_fences(raw))
        if valid_domains(domains, blueprint):
            return sorted(domains, key=lambda item: item["study_order"])
    except Exception:
        pass
    return _fallback_curriculum(blueprint, learning_style)


def _fallback_for_exam(exam_id: str) -> list[dict]:
    try:
        return _fallback_curriculum(load_artifact_from_file(exam_id)["domains"], "mixed_review")
    except Exception:
        return default_curriculum()


def _active_domains(curriculum: dict[str, Any] | None, exam_id: str) -> list[dict]:
    return curriculum["domains"] if curriculum else _fallback_for_exam(exam_id)


async def active_domains_for(user_id: str, exam_id: str) -> list[dict]:
    curriculum = await get_active_curriculum(user_id, exam_id)
    return _active_domains(curriculum, exam_id)


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
    if not row:
        return ""
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


async def choose_today_target(user_id: str, exam_id: str) -> dict[str, Any]:
    curriculum = await get_active_curriculum(user_id, exam_id)
    domains = _active_domains(curriculum, exam_id)
    domain_stats = await performance_map(user_id, exam_id)
    topic_stats = await topic_performance_map(user_id, exam_id)
    return select_today_target(
        domains,
        domain_stats,
        topic_stats,
        curriculum["id"] if curriculum else "",
    )


async def choose_rechallenge_target(
    user_id: str,
    exam_id: str,
    domain: str,
    previous_topic: str,
    previous_task_statement_id: str = "",
) -> dict[str, Any]:
    curriculum = await get_active_curriculum(user_id, exam_id)
    domains = _active_domains(curriculum, exam_id)
    topic_stats = await topic_performance_map(user_id, exam_id)
    return select_rechallenge_target(
        domains,
        domain,
        previous_topic,
        previous_task_statement_id,
        topic_stats,
        curriculum["id"] if curriculum else "",
    )


async def dashboard_summary(
    user_id: str,
    exam_id: str,
    timezone_name: str = "UTC",
) -> dict[str, Any]:
    curriculum = await get_active_curriculum(user_id, exam_id)
    domains = _active_domains(curriculum, exam_id)
    stats = await performance_map(user_id, exam_id)
    topic_stats = await topic_performance_map(user_id, exam_id)
    overview = domain_overview(domains, stats, topic_stats)
    persisted_score = await read_readiness_score(user_id, exam_id)
    readiness = persisted_score["score"] if persisted_score else calculate_readiness(domains, stats)[0]
    rex_record = await read_rex_record(user_id, exam_id)
    streak = await read_session_streak(user_id, exam_id, timezone_name)
    today = await choose_today_target(user_id, exam_id)
    return {
        "exam_id": exam_id,
        "readiness_score": readiness,
        "today_domain": today["domain"],
        "today_topic": today["topic"],
        "rex_record": rex_record,
        "streak": streak,
        "domains": overview,
    }


async def progress_map(user_id: str, exam_id: str) -> dict[str, Any]:
    summary = await dashboard_summary(user_id, exam_id)
    topic_stats = await topic_performance_map(user_id, exam_id)
    return {"domains": coverage_matrix(summary["domains"], topic_stats)}

def _coerce_domains(value: Any) -> list[dict]:
    return json.loads(value) if isinstance(value, str) else value
