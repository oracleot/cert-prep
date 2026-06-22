"""Shared fixtures for concept selector tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from concepts.loader import load_all_concepts


@pytest.fixture
def deployment_concepts():
    """All ready Deployment-domain concepts from dva-c02."""
    return [c for c in load_all_concepts("dva-c02") if c["domain"] == "Deployment"]
