"""Task 9.6c — Readiness score formula unchanged (only outcome counts).

AC3: Concept miss tracking must not affect domain-level readiness math.
missed_criteria and triggered_traps are internal-only.

All tests compile and run; they fail until 9.6 is implemented.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

# ---------------------------------------------------------------------------
# Scope: actual readiness math files only (NOT tests or persistence repos)
# ---------------------------------------------------------------------------
# readiness_readiness math lives in these files:
_READINESS_MATH_FILES = [
    _AGENTS_DIR / "concepts" / "selector.py",
    _AGENTS_DIR / "concepts" / "loader.py",
    _AGENTS_DIR / "nodes" / "coach_open.py",
    _AGENTS_DIR / "performance_repository.py",
    _AGENTS_DIR / "curriculum_progress.py",
    _AGENTS_DIR / "readiness.py",
]
# Only scan files that actually exist.
_READINESS_FILES_EXISTING = [f for f in _READINESS_MATH_FILES if f.exists()]


# ---------------------------------------------------------------------------
# AC3 — Readiness score formula unchanged
# ---------------------------------------------------------------------------

class TestAC3_ReadinessScoreUnchanged:
    """Concept miss fields must not appear in readiness computation."""

    def test_readiness_considers_only_outcome(self):
        """Readiness math must use only 'outcome', not missed_criteria/triggered_traps."""
        for path in _READINESS_FILES_EXISTING:
            content = path.read_text()
            assert "missed_criteria" not in content, (
                f"{path.name} must not reference 'missed_criteria' "
                "(readiness formula must use only outcome)"
            )
            assert "triggered_traps" not in content, (
                f"{path.name} must not reference 'triggered_traps' "
                "(readiness formula must use only outcome)"
            )

    def test_exchange_miss_fields_not_in_readiness_files(self):
        """missed_criteria and triggered_traps must not appear alongside
        readiness computation in any readiness math file."""
        for path in _READINESS_FILES_EXISTING:
            content = path.read_text()
            if "readiness" not in content.lower():
                continue
            lines = [
                (i + 1, line) for i, line in enumerate(content.splitlines())
                if "missed_criteria" in line or "triggered_traps" in line
            ]
            assert not lines, (
                f"{path.relative_to(_AGENTS_DIR)} contains readiness code "
                f"referencing miss fields: {lines}"
            )
