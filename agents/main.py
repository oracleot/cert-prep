from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from db import (
    close_pool,
    init_checkpointer,
    init_pool,
    run_migrations,
    setup_checkpointer_tables,
)
from exam_artifacts import ensure_seeded
from routes.dashboard import router as dashboard_router
from routes.history import router as history_router
from routes.jobs import router as jobs_router
from routes.onboarding import router as onboarding_router
from routes.session import router as session_router

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env.local")
load_dotenv(PROJECT_ROOT / ".env")


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set.")
    return value


@asynccontextmanager
async def lifespan(app: FastAPI):
    _required_env("OPENROUTER_API_KEY")
    await init_pool()
    await init_checkpointer()
    try:
        await run_migrations()
        await setup_checkpointer_tables()
    except Exception:
        logger.exception("Database setup failed. Continuing with degraded persistence.")
    try:
        seeded = await ensure_seeded()
        if seeded:
            logger.info("Seeded %d exam artifact(s) into the DB cache.", seeded)
    except Exception:
        logger.exception("Exam artifact seeding failed; continuing with file-only reads.")
    try:
        yield
    finally:
        await close_pool()


app = FastAPI(title="Gauntlet LangGraph Service", lifespan=lifespan)
app.include_router(dashboard_router)
app.include_router(history_router)
app.include_router(jobs_router)
app.include_router(onboarding_router)
app.include_router(session_router)


class HealthResponse(BaseModel):
    status: str
    openrouter_configured: bool
    database_configured: bool


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        openrouter_configured=bool(os.environ.get("OPENROUTER_API_KEY")),
        database_configured=bool(os.environ.get("DATABASE_URL")),
    )
