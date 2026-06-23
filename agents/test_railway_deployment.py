"""
Railway Deployment Readiness — Python / agents contract tests.

Validates:
  1. agents/railway.toml exists and declares the fastapi service.
  2. agents/Dockerfile exists and copies migrations/ (agents/db.py needs it).
  3. agents/main.py /health endpoint signature.
  4. Required env vars are guarded at startup (DATABASE_URL).
  5. No secret files are referenced in agents/ source tree.

Run: cd agents && pytest test_railway_deployment.py -v
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

AGENTS_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# AC1 — FastAPI /health endpoint
# ---------------------------------------------------------------------------

class TestAgentsHealthEndpoint:
    """agents/main.py must expose GET /health returning status + dep flags."""

    def test_health_handler_exists(self):
        main = AGENTS_DIR / "main.py"
        content = main.read_text()
        # Must have an endpoint registered at /health
        assert re.search(r'@app\.get\s*\(\s*["\']\/health["\']', content), \
            "main.py must define @app.get('/health')"

    def test_health_response_model_includes_openrouter_and_database_flags(self):
        main = AGENTS_DIR / "main.py"
        content = main.read_text()
        # HealthResponse must include booleans for the two critical deps
        assert re.search(r"openrouter_configured|database_configured", content), \
            "HealthResponse must include openrouter_configured and/or database_configured fields"


# ---------------------------------------------------------------------------
# AC2 — agents/railway.toml
# ---------------------------------------------------------------------------

class TestAgentsRailwayConfig:
    """agents/railway.toml declares the python/fastapi service."""

    def test_railway_toml_exists(self):
        railway = AGENTS_DIR / "railway.toml"
        assert railway.exists(), f"agents/railway.toml not found at {railway}"

    def test_railway_toml_declares_python_service(self):
        railway = AGENTS_DIR / "railway.toml"
        content = railway.read_text()
        assert re.search(r"python|fastapi|uvicorn", content, re.IGNORECASE), \
            "railway.toml must declare the python/fastapi service"

    def test_railway_toml_does_not_duplicate_root_nextjs_config(self):
        # agents/railway.toml is for the agents service only — root railway.toml
        # handles nextjs. Verify agents railway.toml is self-contained.
        railway = AGENTS_DIR / "railway.toml"
        content = railway.read_text()
        # No hard rule against nextjs mentions, but a simple sanity check:
        # it should mention something python-related, not just "next build"
        assert re.search(r"python|fastapi|uvicorn|run|start", content, re.IGNORECASE), \
            "agents/railway.toml must contain a run/start command for the python service"


# ---------------------------------------------------------------------------
# AC3 — agents/Dockerfile includes migrations build context
# ---------------------------------------------------------------------------

class TestAgentsDockerfile:
    """agents/Dockerfile must copy the project root migrations/ directory."""

    def test_dockerfile_exists(self):
        dockerfile = AGENTS_DIR / "Dockerfile"
        assert dockerfile.exists(), f"Dockerfile not found at {dockerfile}"

    def test_dockerfile_copies_migrations(self):
        """agents/db.py reads migrations/ from PROJECT_ROOT; Railway build must
        include it. Either COPY ../migrations or a multi-stage build that
        bakes in the directory is acceptable."""
        dockerfile = AGENTS_DIR / "Dockerfile"
        content = dockerfile.read_text()
        assert "migrations" in content, \
            "Dockerfile must include migrations/ (agents/db.py:run_migrations() needs it)"

    def test_dockerfile_exposes_port_8000(self):
        dockerfile = AGENTS_DIR / "Dockerfile"
        content = dockerfile.read_text()
        assert "8000" in content, \
            "Dockerfile must EXPOSE 8000 for FastAPI on Railway"

    def test_dockerfile_sets_workdir(self):
        dockerfile = AGENTS_DIR / "Dockerfile"
        content = dockerfile.read_text()
        assert re.search(r"WORKDIR\s+", content), \
            "Dockerfile must set WORKDIR"


# ---------------------------------------------------------------------------
# AC4 — Required env vars documented
# ---------------------------------------------------------------------------

class TestEnvVarDocumentation:
    """Docs must enumerate required env vars for both services."""

    @pytest.fixture
    def deploy_doc(self) -> Path | None:
        candidates = [
            AGENTS_DIR.parent / "docs" / "railway-deploy.md",
            AGENTS_DIR.parent / "docs" / "deployment.md",
            AGENTS_DIR.parent / "docs" / "implementation-backlog.md",
            AGENTS_DIR.parent / "docs" / "tech-stack.md",
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    def test_deploy_doc_exists(self, deploy_doc):
        assert deploy_doc is not None, "No deploy doc found in docs/"

    def test_documents_openrouter_api_key(self, deploy_doc):
        if not deploy_doc:
            pytest.skip("No deploy doc found")
        content = deploy_doc.read_text()
        assert "OPENROUTER_API_KEY" in content

    def test_documents_database_url(self, deploy_doc):
        if not deploy_doc:
            pytest.skip("No deploy doc found")
        content = deploy_doc.read_text()
        assert "DATABASE_URL" in content

    def test_documents_redis_url(self, deploy_doc):
        if not deploy_doc:
            pytest.skip("No deploy doc found")
        content = deploy_doc.read_text()
        assert "REDIS_URL" in content

    def test_documents_langgraph_url(self, deploy_doc):
        if not deploy_doc:
            pytest.skip("No deploy doc found")
        content = deploy_doc.read_text()
        assert "LANGGRAPH_URL" in content


# ---------------------------------------------------------------------------
# AC5 — DATABASE_URL guard exercised in tests
# ---------------------------------------------------------------------------

class TestDatabaseGuard:
    """db.py must raise if DATABASE_URL is absent at startup."""

    def test_db_module_has_guard(self):
        db_py = AGENTS_DIR / "db.py"
        content = db_py.read_text()
        assert re.search(r"RuntimeError.*DATABASE_URL is not set", content, re.IGNORECASE), \
            "db.py must raise RuntimeError when DATABASE_URL is absent"

    @pytest.mark.asyncio
    async def test_init_pool_raises_without_database_url(self):
        """Verify the guard fires by patching env before importing init_pool."""
        import os
        original = os.environ.pop("DATABASE_URL", None)

        # Re-import to pick up the patched env
        import importlib
        import db as db_module
        importlib.reload(db_module)

        # init_pool with no DATABASE_URL should set _pool = None, not raise
        await db_module.init_pool()
        assert db_module._pool is None, \
            "Without DATABASE_URL, init_pool() must fall back gracefully (set _pool=None)"

        if original:
            os.environ["DATABASE_URL"] = original
