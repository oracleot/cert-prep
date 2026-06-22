"""Shared pytest fixtures for agents/concepts/ tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure agents/ is on the path
_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

CONCEPTS_DATA = _AGENTS_DIR / "data" / "concepts"


@pytest.fixture
def concepts_data_dir() -> Path:
    return CONCEPTS_DATA
