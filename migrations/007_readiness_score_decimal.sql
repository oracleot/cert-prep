-- Migration 007: Allow fractional readiness percentages

ALTER TABLE readiness_scores DROP CONSTRAINT IF EXISTS readiness_scores_score_check;
ALTER TABLE readiness_scores ALTER COLUMN score TYPE NUMERIC(5,2) USING score::numeric;
ALTER TABLE readiness_scores ALTER COLUMN score SET DEFAULT 0;
ALTER TABLE readiness_scores ADD CONSTRAINT readiness_scores_score_check CHECK (score >= 0 AND score <= 100);
