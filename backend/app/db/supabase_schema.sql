-- FounderOS AI — Supabase Schema
-- Run this in your Supabase SQL editor to set up the database.

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Generations ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS generations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type            TEXT NOT NULL CHECK (type IN ('prd', 'roadmap', 'architecture', 'pitch_deck', 'market_analysis')),
    input_data      JSONB NOT NULL DEFAULT '{}',
    output_content  TEXT,
    user_id         UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    workflow_run_id UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_generations_user_id   ON generations(user_id);
CREATE INDEX IF NOT EXISTS idx_generations_type       ON generations(type);
CREATE INDEX IF NOT EXISTS idx_generations_created_at ON generations(created_at DESC);

-- ── Workflow Runs ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS workflow_runs (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_name  TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    input_data     JSONB NOT NULL DEFAULT '{}',
    output_data    JSONB NOT NULL DEFAULT '{}',
    steps          JSONB NOT NULL DEFAULT '[]',
    user_id        UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    error          TEXT,
    started_at     TIMESTAMPTZ,
    completed_at   TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflow_runs_user_id ON workflow_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_status  ON workflow_runs(status);

-- ── Row Level Security ────────────────────────────────────────────────────────

ALTER TABLE generations    ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_runs  ENABLE ROW LEVEL SECURITY;

-- Users can only read and insert their own generations
CREATE POLICY "generations_select_own" ON generations FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "generations_insert_own" ON generations FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can only read their own workflow runs
CREATE POLICY "workflow_runs_select_own" ON workflow_runs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "workflow_runs_insert_own" ON workflow_runs FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ── Auto-update updated_at ────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER generations_updated_at
    BEFORE UPDATE ON generations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
