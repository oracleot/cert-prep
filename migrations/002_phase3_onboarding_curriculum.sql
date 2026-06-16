-- Migration 002: Phase 3 onboarding, curriculum, and progress tables

CREATE TABLE IF NOT EXISTS onboarding_runs (
  id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        TEXT        NOT NULL,
  exam_id        TEXT        NOT NULL,
  exam_name      TEXT        NOT NULL,
  learning_style TEXT        NOT NULL,
  status         TEXT        NOT NULL DEFAULT 'intake',
  step           TEXT        NOT NULL DEFAULT 'exam_input',
  blueprint      JSONB,
  curriculum_id  UUID,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS onboarding_runs_user_id_idx
  ON onboarding_runs(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS agent_feed_events (
  id                BIGSERIAL   PRIMARY KEY,
  onboarding_run_id UUID        NOT NULL REFERENCES onboarding_runs(id) ON DELETE CASCADE,
  agent             TEXT        NOT NULL,
  status            TEXT        NOT NULL CHECK (status IN ('running', 'complete', 'failed')),
  message           TEXT        NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS agent_feed_events_run_id_idx
  ON agent_feed_events(onboarding_run_id, id);

CREATE TABLE IF NOT EXISTS curricula (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           TEXT        NOT NULL,
  exam_id           TEXT        NOT NULL,
  onboarding_run_id UUID        REFERENCES onboarding_runs(id) ON DELETE SET NULL,
  domains           JSONB       NOT NULL,
  active            BOOLEAN     NOT NULL DEFAULT TRUE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS curricula_user_exam_active_idx
  ON curricula(user_id, exam_id, active);

CREATE TABLE IF NOT EXISTS performance_aggregates (
  user_id       TEXT        NOT NULL,
  exam_id       TEXT        NOT NULL,
  domain        TEXT        NOT NULL,
  correct_count INTEGER     NOT NULL DEFAULT 0,
  total_count   INTEGER     NOT NULL DEFAULT 0,
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, exam_id, domain)
);

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS topic TEXT;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS curriculum_id UUID REFERENCES curricula(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS sessions_curriculum_id_idx ON sessions(curriculum_id);
