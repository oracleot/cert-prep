-- Migration 011: Phase 9 — concept miss tracking + resource metadata on exchanges
-- Issue 9.6 (internal concept miss tracking) and 9.5 (Sage Review next resource audit).
--
-- All columns are additive and nullable/JSONB-defaulted so existing rows remain
-- valid without a backfill. Concept-level tracking is kept independent of the
-- domain-level readiness formula (which only reads `outcome`).

ALTER TABLE exchanges
  ADD COLUMN IF NOT EXISTS missed_criteria     JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS triggered_traps     JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS official_docs       JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS skill_builder_links JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS lab_links           JSONB NOT NULL DEFAULT '[]'::jsonb;

-- GIN indexes support containment queries used by the concept-miss audit
-- (e.g. WHERE missed_criteria @> '["CodeBuild defaults to no VPC"]'::jsonb).
-- GIN on JSONB also accelerates "rows with any entry" probes with jsonb_array_length.
CREATE INDEX IF NOT EXISTS exchanges_missed_criteria_gin_idx
  ON exchanges USING GIN (missed_criteria);

CREATE INDEX IF NOT EXISTS exchanges_triggered_traps_gin_idx
  ON exchanges USING GIN (triggered_traps);
