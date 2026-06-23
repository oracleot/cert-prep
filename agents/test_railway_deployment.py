"""
Railway Deployment Readiness — Python / agents contract tests.

Validates:
  1. agents/main.py /health endpoint signature.
  2. agents/railway.toml (agents + root) uses Railway schema camelCase keys.

Run: cd agents && pytest test_railway_deployment.py -v
"""
from __future__ import annotations

import re
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
        assert re.search(r'@app\.get\s*\(\s*["\']\/health["\']', content), \
            "main.py must define @app.get('/health')"

    def test_health_response_model_includes_openrouter_and_database_flags(self):
        main = AGENTS_DIR / "main.py"
        content = main.read_text()
        assert re.search(r"openrouter_configured|database_configured", content), \
            "HealthResponse must include openrouter_configured and/or database_configured fields"


# ---------------------------------------------------------------------------
# AC1b — root Next.js railway.toml (from agents/ perspective)
# ---------------------------------------------------------------------------

class TestRootRailwayConfig:
    """Validates the project-root railway.toml uses Railway schema camelCase keys."""

    def test_root_railway_toml_exists(self):
        root_railway = AGENTS_DIR.parent / "railway.toml"
        assert root_railway.exists(), f"root railway.toml not found at {root_railway}"

    def test_root_railway_uses_camelcase_deploy_keys(self):
        root_railway = AGENTS_DIR.parent / "railway.toml"
        content = root_railway.read_text()
        for key in ["healthcheckPath", "healthcheckTimeout", "restartPolicyType", "restartPolicyMaxRetries"]:
            assert key in content, f"root railway.toml must use Railway schema key: {key}"
        assert "healthcheck_path" not in content
        assert "healthcheck_timeout" not in content

    def test_root_railway_uses_buildCommand_not_snake_case(self):
        root_railway = AGENTS_DIR.parent / "railway.toml"
        content = root_railway.read_text()
        assert "buildCommand" in content, "root railway.toml must use Railway schema key: buildCommand"
        assert "build_command" not in content

    def test_root_railway_has_no_deployments_block(self):
        root_railway = AGENTS_DIR.parent / "railway.toml"
        content = root_railway.read_text()
        assert "[deployments]" not in content, \
            "root railway.toml must not contain [deployments] block (invalid Railway schema)"


# ---------------------------------------------------------------------------
# AC2 — agents/railway.toml
# ---------------------------------------------------------------------------

class TestAgentsRailwayConfig:
    """agents/railway.toml declares the python/fastapi service."""

    def test_railway_toml_exists(self):
        railway = AGENTS_DIR / "railway.toml"
        assert railway.exists(), f"agents/railway.toml not found at {railway}"

    def test_railway_toml_uses_camelcase_deploy_keys(self):
        railway = AGENTS_DIR / "railway.toml"
        content = railway.read_text()
        for key in ["healthcheckPath", "healthcheckTimeout", "restartPolicyType", "restartPolicyMaxRetries"]:
            assert key in content, f"agents/railway.toml must use Railway schema key: {key}"
        assert "healthcheck_path" not in content
        assert "healthcheck_timeout" not in content
        assert "restart_policy_type" not in content
        assert "restart_policy_max_retries" not in content

    def test_railway_toml_uses_dockerfilePath_not_snake_case(self):
        railway = AGENTS_DIR / "railway.toml"
        content = railway.read_text()
        assert "dockerfilePath" in content, "agents/railway.toml must use Railway schema key: dockerfilePath"
        assert "dockerfile_path" not in content

    def test_railway_toml_declares_python_service(self):
        railway = AGENTS_DIR / "railway.toml"
        content = railway.read_text()
        assert re.search(r"python|fastapi|uvicorn", content, re.IGNORECASE), \
            "railway.toml must declare the python/fastapi service"
