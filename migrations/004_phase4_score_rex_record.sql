-- Migration 004: Phase 4 readiness score + Rex record persistence

CREATE TABLE IF NOT EXISTS readiness_scores (
  user_id    TEXT        NOT NULL,
  exam_id    TEXT        NOT NULL,
  score      INTEGER     NOT NULL DEFAULT 0 CHECK (score >= 0 AND score <= 100),
  breakdown  JSONB       NOT NULL DEFAULT '[]'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, exam_id)
);

CREATE TABLE IF NOT EXISTS rex_record (
  user_id    TEXT        NOT NULL,
  exam_id    TEXT        NOT NULL,
  user_wins  INTEGER     NOT NULL DEFAULT 0,
  rex_wins   INTEGER     NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, exam_id)
);
