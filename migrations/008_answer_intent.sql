-- Migration 008: track answer intent for knowledge-gap submissions.

ALTER TABLE exchanges
  ADD COLUMN IF NOT EXISTS answer_intent TEXT NOT NULL DEFAULT 'attempt'
  CHECK (answer_intent IN ('attempt', 'knowledge_gap'));
