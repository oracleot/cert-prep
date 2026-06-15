from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from db import close_pool, init_pool
from routes.session import router as session_router

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
    _required_env("DATABASE_URL")
    await init_pool()
    try:
        yield
    finally:
        await close_pool()


app = FastAPI(title="Gauntlet LangGraph Service", lifespan=lifespan)
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
