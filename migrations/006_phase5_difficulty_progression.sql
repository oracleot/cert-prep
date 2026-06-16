-- Migration 006: Phase 5 per-domain difficulty progression

CREATE TABLE IF NOT EXISTS domain_difficulty_progress (
  user_id              TEXT        NOT NULL,
  exam_id              TEXT        NOT NULL,
  domain               TEXT        NOT NULL,
  difficulty           TEXT        NOT NULL DEFAULT 'easy'
    CHECK (difficulty IN ('easy', 'medium', 'hard')),
  high_accuracy_streak INTEGER     NOT NULL DEFAULT 0,
  low_accuracy_streak  INTEGER     NOT NULL DEFAULT 0,
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, exam_id, domain)
);
