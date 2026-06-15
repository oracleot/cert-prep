-- Migration 001: initial schema
-- LangGraph checkpointer tables are created by checkpointer.setup()
-- This file covers application domain tables.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS sessions (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     TEXT        NOT NULL,
  exam_id     TEXT        NOT NULL,
  domain      TEXT        NOT NULL,
  started_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS sessions_user_id_idx ON sessions(user_id);

CREATE TABLE IF NOT EXISTS exchanges (
  id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id   UUID        REFERENCES sessions(id) ON DELETE CASCADE,
  cycle        INTEGER     NOT NULL,
  domain       TEXT        NOT NULL,
  topic        TEXT        NOT NULL,
  challenge    JSONB       NOT NULL,
  user_answer  TEXT        NOT NULL,
  outcome      TEXT        NOT NULL CHECK (outcome IN ('correct', 'incorrect')),
  sage_response TEXT       NOT NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS exchanges_session_id_idx ON exchanges(session_id);
