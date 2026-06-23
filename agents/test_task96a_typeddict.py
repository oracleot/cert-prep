"""Task 9.6a — Exchange TypedDict carries miss field annotations.

AC1: Exchange TypedDict and sage_respond output include miss fields.

All tests compile and run; they fail until 9.6 is implemented.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))


class TestAC1_ExchangeTypedDictAnnotations:
    """Exchange TypedDict must declare missed_criteria and triggered_traps."""

    def test_exchange_typeddict_has_missed_criteria(self):
        """Exchange TypedDict in state.py must declare missed_criteria field."""
        from state import Exchange

        hints = getattr(Exchange, "__annotations__", {})
        assert "missed_criteria" in hints, (
            "Exchange TypedDict must have 'missed_criteria' annotation"
        )

    def test_exchange_typeddict_has_triggered_traps(self):
        """Exchange TypedDict in state.py must declare triggered_traps field."""
        from state import Exchange

        hints = getattr(Exchange, "__annotations__", {})
        assert "triggered_traps" in hints, (
            "Exchange TypedDict must have 'triggered_traps' annotation"
        )
