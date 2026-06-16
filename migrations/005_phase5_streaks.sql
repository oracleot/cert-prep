-- Migration 005: Phase 5 daily session streaks

CREATE TABLE IF NOT EXISTS session_streaks (
  user_id           TEXT        NOT NULL,
  exam_id           TEXT        NOT NULL,
  current_streak    INTEGER     NOT NULL DEFAULT 0,
  last_completed_on DATE,
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, exam_id)
);
