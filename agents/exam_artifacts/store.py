"""Postgres-backed runtime cache for exam artifacts.

The JSON files in ``agents/data/exam_artifacts/`` are the source of truth. This
module upserts them into the ``exam_artifacts`` table on service boot and reads
them back at request time. Reads fall through to the file system when the DB
row is missing or the pool is unavailable, so dev/test never depends on a live
DB.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from db import get_pool, has_pool

from .loader import (
    ARTIFACT_DIR,
    content_checksum,
    list_artifact_files,
    load_artifact_from_file,
    validate_artifact_shape,
)

logger = logging.getLogger(__name__)


async def ensure_seeded() -> int:
    """Upsert every JSON artifact into ``exam_artifacts``. Returns rows touched.

    Idempotent — re-runs cleanly on every boot. Skips rows whose
    ``content_checksum`` already matches.
    """
    if not has_pool():
        return 0
    if not ARTIFACT_DIR.exists():
        logger.warning("No artifact directory at %s — skipping seed", ARTIFACT_DIR)
        return 0

    seeded = 0
    pool = get_pool()
    for exam_id in list_artifact_files():
        try:
            artifact = load_artifact_from_file(exam_id)
            errors = validate_artifact_shape(artifact)
            if errors:
                logger.error("Skipping %s: shape errors: %s", exam_id, errors)
                continue
            checksum = content_checksum(exam_id)
            async with pool.connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO exam_artifacts (
                        exam_code, canonical_name, provider, official_guide_url,
                        captured_at, source_version, content_checksum, domains, is_active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                    ON CONFLICT (exam_code) DO UPDATE SET
                        canonical_name = EXCLUDED.canonical_name,
                        provider = EXCLUDED.provider,
                        official_guide_url = EXCLUDED.official_guide_url,
                        captured_at = EXCLUDED.captured_at,
                        source_version = EXCLUDED.source_version,
                        content_checksum = EXCLUDED.content_checksum,
                        domains = EXCLUDED.domains,
                        is_active = TRUE,
                        updated_at = NOW()
                    WHERE exam_artifacts.content_checksum IS DISTINCT FROM EXCLUDED.content_checksum
                    """,
                    (
                        artifact["exam_code"],
                        artifact["canonical_name"],
                        artifact["provider"],
                        artifact["official_guide_url"],
                        artifact["captured_at"],
                        artifact["source_version"],
                        checksum,
                        json.dumps(artifact["domains"]),
                    ),
                )
                await conn.commit()
            seeded += 1
        except Exception:
            logger.exception("Failed to seed artifact %s", exam_id)
    return seeded


async def get_artifact(exam_id: str) -> dict[str, Any] | None:
    """Read an artifact from the DB. Falls back to None if the pool is down."""
    if not has_pool():
        return None
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT exam_code, canonical_name, provider, official_guide_url, "
                "captured_at, source_version, content_checksum, domains "
                "FROM exam_artifacts WHERE exam_code = %s AND is_active = TRUE",
                (exam_id,),
            )
            row = await cur.fetchone()
    if not row:
        return None
    return {
        "exam_code": row[0],
        "canonical_name": row[1],
        "provider": row[2],
        "official_guide_url": row[3],
        "captured_at": row[4].isoformat() if row[4] else None,
        "source_version": row[5],
        "content_checksum": row[6],
        "domains": json.loads(row[7]) if isinstance(row[7], str) else row[7],
    }


async def list_supported_exams() -> list[dict[str, Any]]:
    """List every active artifact, ordered by exam_code."""
    if not has_pool():
        return []
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT exam_code, canonical_name, provider FROM exam_artifacts "
                "WHERE is_active = TRUE ORDER BY exam_code"
            )
            rows = await cur.fetchall()
    return [
        {"exam_code": r[0], "canonical_name": r[1], "provider": r[2]} for r in rows
    ]
