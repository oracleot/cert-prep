"""
Docker import smoke test — mirrors container WORKDIR /app/agents semantics.

In Docker the container runs:
    WORKDIR /app/agents
    CMD ["python", "-m", "uvicorn", "main:app", ...]

Python resolves `main` relative to the cwd (/app/agents), and bare imports
(e.g. `from db import ...`) are resolved against sys.path[0] = '' (cwd).

This test simulates that environment so bare-import regressions are caught
without a full Docker build.

Run: cd agents && python test_docker_import_smoke.py
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent
CONTAINER_CWD = Path("/app/agents")


def test_main_imports_from_container_workdir():
    """
    Simulate: cd /app/agents && python -c "import main"
    sys.path[0] == '' (cwd), cwd is /app/agents equivalent.
    """
    original_cwd = os.getcwd()
    original_path = sys.path.copy()

    try:
        os.chdir(AGENTS_DIR)
        # Mirrors how Python sets sys.path[0] = '' when -m is used from cwd
        sys.path = [str(AGENTS_DIR)] + [p for p in sys.path if p != str(AGENTS_DIR)]

        # Re-import must not raise ModuleNotFoundError for bare imports
        import importlib
        import main as main_mod
        importlib.reload(main_mod)
        assert hasattr(main_mod, "app"), "main module must expose 'app' FastAPI instance"
    finally:
        os.chdir(original_cwd)
        sys.path = original_path


def test_bare_imports_resolve_under_agents_workdir():
    """
    Verify bare imports like `from db import ...` resolve correctly when
    sys.path[0] points at the agents directory (container WORKDIR semantics).
    """
    original_cwd = os.getcwd()
    original_path = sys.path.copy()

    try:
        os.chdir(AGENTS_DIR)
        sys.path = [str(AGENTS_DIR)] + [p for p in sys.path if p != str(AGENTS_DIR)]

        # These are the bare imports used throughout agents/ source
        import db
        import routes.session
        import graphs.session
        import state
        import llm

        # Smoke: each module must expose something callable / structured
        assert callable(db.get_pool) or callable(db.init_pool), "db must expose pool helpers"
        assert hasattr(routes.session, "router"), "routes.session must expose a router"
        assert callable(graphs.session.get_session_graph), "graphs.session must expose graph factory"
        assert callable(state.initial_state), "state must expose initial_state"
        assert callable(llm.llm_runtime), "llm must expose llm_runtime"
    finally:
        os.chdir(original_cwd)
        sys.path = original_path


if __name__ == "__main__":
    import traceback

    errors = []
    for test_fn in [test_main_imports_from_container_workdir, test_bare_imports_resolve_under_agents_workdir]:
        try:
            test_fn()
            print(f"PASS: {test_fn.__name__}")
        except Exception as e:
            print(f"FAIL: {test_fn.__name__}: {e}")
            traceback.print_exc()
            errors.append(e)

    if errors:
        print(f"\n{len(errors)} test(s) failed.")
        sys.exit(1)
    else:
        print("\nAll smoke tests passed.")
