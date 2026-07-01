-- Migration 013: Phase 11 — Option-Based Session Mode
-- Issue 11.1–11.6: prompts carry response_mode + 4 labeled A/B/C/D options +
-- answer_key; learners answer by selection; verdict payload exposes chosen /
-- correct / missed / incorrect labels immediately.
--
-- All columns are additive and JSONB-defaulted so existing rows remain valid.
-- The mode/options/answer_key already travel inside the `challenge` JSONB
-- (rex_challenge writes them there); the dedicated columns exist so
-- history views can render the verdict overlay without re-parsing challenge
-- JSONB and so dashboards can group by response_mode cheaply.

ALTER TABLE exchanges
  ADD COLUMN IF NOT EXISTS response_mode     TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS options           JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS answer_key        JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS selected_labels   JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS correct_labels    JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS missed_labels     JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS incorrect_labels  JSONB NOT NULL DEFAULT '[]'::jsonb;

-- Cheap grouping by mode for analytics ("how many multi-response prompts
-- have we served today?"). Partial index excludes empty-mode rows so the
-- index stays small for pre-Phase 11 exchanges.
CREATE INDEX IF NOT EXISTS exchanges_response_mode_idx
  ON exchanges(response_mode)
  WHERE response_mode <> '';

-- GIN on the label arrays accelerates "did the learner pick C?" style lookups.
CREATE INDEX IF NOT EXISTS exchanges_selected_labels_gin_idx
  ON exchanges USING GIN (selected_labels);
CREATE INDEX IF NOT EXISTS exchanges_missed_labels_gin_idx
  ON exchanges USING GIN (missed_labels);