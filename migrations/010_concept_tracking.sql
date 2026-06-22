-- Migration 010: track concept_id through sessions and exchanges
-- Required for 9.3: closed-book concept selection.
-- Nullable for backward compatibility during rollout.

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS concept_id TEXT;
ALTER TABLE exchanges ADD COLUMN IF NOT EXISTS concept_id TEXT;

CREATE INDEX IF NOT EXISTS sessions_concept_id_idx ON sessions(concept_id) WHERE concept_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS exchanges_concept_id_idx ON exchanges(concept_id) WHERE concept_id IS NOT NULL;
