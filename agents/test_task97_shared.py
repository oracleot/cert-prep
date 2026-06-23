"""Shared fixtures for Task 9.7 — Eval harness tests."""
from __future__ import annotations

import sys
from pathlib import Path

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


def _fake_concept(**overrides) -> dict:
    """Minimal concept record fixture for eval harness tests."""
    base = {
        "id": "deploy-codepipeline-basics",
        "domain": "Deployment",
        "topic": "CodePipeline Basics",
        "official_docs": ["https://docs.aws.amazon.com/codepipeline/latest/userguide/"],
        "skill_builder_links": ["https://skillbuilder.aws/labs/"],
        "lab_links": ["https://clouderlabs.example.com/codepipeline-lab"],
    }
    base.update(overrides)
    return base
