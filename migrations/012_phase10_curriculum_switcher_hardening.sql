-- Migration 012: Phase 10 — harden the one-active-curriculum invariant
-- for the V1 curriculum switcher (AGENTS.md "Narrow exception: cross-exam
-- curriculum switcher", 2026-06-26). Today the invariant
-- "exactly one active curriculum per (user_id, exam_id)" is enforced by
-- application logic in curriculum_repository.create_curriculum(). This
-- migration replaces the loose composite index with a partial UNIQUE
-- index so the constraint is also enforced at the DB layer.

DROP INDEX IF EXISTS curricula_user_exam_active_idx;

CREATE UNIQUE INDEX IF NOT EXISTS curricula_one_active_per_user_exam_idx
  ON curricula(user_id, exam_id)
  WHERE active IS TRUE;
