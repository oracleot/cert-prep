-- Migration 003: Phase 7 — exam artifact model + Sage citation storage
-- See docs/implementation-backlog.md (7.2) and docs/exam-reliability-rubric.md (R1, R5.6).

CREATE TABLE IF NOT EXISTS exam_artifacts (
  id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  exam_code          TEXT        NOT NULL UNIQUE,
  canonical_name     TEXT        NOT NULL,
  provider           TEXT        NOT NULL,
  official_guide_url TEXT        NOT NULL,
  captured_at        DATE        NOT NULL,
  source_version     TEXT        NOT NULL,
  content_checksum   TEXT        NOT NULL,
  domains            JSONB       NOT NULL,
  is_active          BOOLEAN     NOT NULL DEFAULT TRUE,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS exam_artifacts_active_idx ON exam_artifacts(is_active);

-- Sage citation storage for 7.6. JSONB array of {url, title, snippet_id} objects.
-- DEFAULT '[]'::jsonb keeps existing rows valid without a backfill.
ALTER TABLE exchanges ADD COLUMN IF NOT EXISTS citations JSONB NOT NULL DEFAULT '[]'::jsonb;
