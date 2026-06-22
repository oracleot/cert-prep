-- Migration 009: capture Sage quality feedback and metric exclusions.

ALTER TABLE exchanges
  ADD COLUMN IF NOT EXISTS review_status TEXT NOT NULL DEFAULT 'active';

ALTER TABLE exchanges DROP CONSTRAINT IF EXISTS exchanges_review_status_check;
ALTER TABLE exchanges
  ADD CONSTRAINT exchanges_review_status_check
  CHECK (review_status IN ('active', 'excluded_pending_review', 'confirmed_hallucination', 'dismissed'));

CREATE TABLE IF NOT EXISTS sage_feedback (
  id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id          UUID        NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  exchange_id         UUID        NOT NULL REFERENCES exchanges(id) ON DELETE CASCADE,
  thread_id           TEXT        NOT NULL,
  user_id             TEXT        NOT NULL,
  exam_id             TEXT        NOT NULL,
  domain              TEXT        NOT NULL,
  topic               TEXT        NOT NULL,
  cycle               INTEGER     NOT NULL,
  feedback_type       TEXT        NOT NULL CHECK (feedback_type IN ('factual_error', 'bad_source', 'confusing_explanation')),
  comment             TEXT        NOT NULL CHECK (char_length(btrim(comment)) BETWEEN 10 AND 1000),
  status              TEXT        NOT NULL DEFAULT 'pending_review'
    CHECK (status IN ('pending_review', 'confirmed_hallucination', 'dismissed')),
  excludes_metrics    BOOLEAN     NOT NULL DEFAULT FALSE,
  metrics_reversed_at TIMESTAMPTZ,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (session_id, cycle)
);

CREATE INDEX IF NOT EXISTS sage_feedback_status_idx ON sage_feedback(status, created_at DESC);
CREATE INDEX IF NOT EXISTS sage_feedback_user_exam_idx ON sage_feedback(user_id, exam_id, created_at DESC);
