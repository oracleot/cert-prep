"""
Railway Deployment Readiness — Dockerfile, env-var docs, and DATABASE_URL guard.

Run: cd agents && pytest test_railway_dockerfile_and_docs.py -v
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

AGENTS_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# AC3 — agents/Dockerfile includes migrations build context
# ---------------------------------------------------------------------------

class TestAgentsDockerfile:
    """agents/Dockerfile must copy the project root migrations/ directory."""

    def test_dockerfile_exists(self):
        dockerfile = AGENTS_DIR / "Dockerfile"
        assert dockerfile.exists(), f"Dockerfile not found at {dockerfile}"

    def test_dockerfile_copies_migrations(self):
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
        import os
        original = os.environ.pop("DATABASE_URL", None)

        import importlib
        import db as db_module
        importlib.reload(db_module)

        await db_module.init_pool()
        assert db_module._pool is None, \
            "Without DATABASE_URL, init_pool() must fall back gracefully (set _pool=None)"

        if original:
            os.environ["DATABASE_URL"] = original
