ADR-0002: Hard-delete completed sessions from history
Status: Accepted
Date: 2026-06-30

## Context
Users want to remove a past study session from history. The request is for a permanent deletion, not a hide/archive state, and only completed sessions are eligible.

## Decision
Add an inline delete action in history for completed sessions only.

Deletion permanently removes the session row and cascades its exchanges and feedback. After deletion, the app recomputes the visible progress aggregates and readiness score for the affected exam.

## Consequences
- History becomes reversible only by re-running a session.
- In-progress sessions stay protected from deletion.
- Deleted sessions may briefly remain in local resumability until the next session restore self-heals the stale thread id.
- Progress totals stay aligned with the remaining session set.
