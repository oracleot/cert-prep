"""Phase 11 — option-based session types and helpers.

Mirror of ``lib/option-types.ts``. Kept as a small module so callers can
``from option_types import ...`` without pulling in app-side imports.

``ResponseMode`` is intentionally a plain string alias rather than a
``Literal`` so it survives serialization round-trips and JSONB persistence
in Postgres without coercion. ``OptionLabel`` is constrained to the four
uppercase letters per the spec.
"""
from __future__ import annotations

from typing import Iterable

# Plain aliases — see module docstring.
ResponseMode = str
OptionLabel = str

OPTION_LABELS: tuple[OptionLabel, ...] = ("A", "B", "C", "D")

# Single correct label or up to two in V1 — exact-match only, no partial credit.
SINGLE_RESPONSE_MAX = 1
MULTI_RESPONSE_MAX = 2


def is_option_label(value: object) -> bool:
    return isinstance(value, str) and value in OPTION_LABELS


def is_response_mode(value: object) -> bool:
    return value in ("single_response", "multiple_response")


def normalize_option_labels(values: Iterable[object]) -> list[OptionLabel]:
    """Stable, deduped, sorted list of option labels — A < B < C < D."""
    seen: set[OptionLabel] = set()
    out: list[OptionLabel] = []
    for value in values:
        if is_option_label(value) and value not in seen:
            seen.add(value)
            out.append(value)
    out.sort()
    return out


def max_labels_for_mode(mode: ResponseMode) -> int:
    return SINGLE_RESPONSE_MAX if mode == "single_response" else MULTI_RESPONSE_MAX