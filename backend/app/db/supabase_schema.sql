-- =============================================================================
-- FounderOS AI — Supabase Schema
-- =============================================================================
-- Run this in the Supabase SQL editor to create all tables, indexes, and RLS
-- policies. Safe to re-run (uses CREATE IF NOT EXISTS).
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Users ────────────────────────────────────────────────────────────────────
-- Mirrors auth.users with app-specific profile data. PK is the auth user id.

CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT NOT NULL UNIQUE,
    full_name   TEXT,
    avatar_url  TEXT,
    metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ── Projects ─────────────────────────────────────────────────────────────────
-- A founder's startup project. Generations are attached to projects.

CREATE TABLE IF NOT EXISTS projects (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    description     TEXT,
    industry        TEXT,
    target_audience TEXT,
    status          TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'archived', 'deleted')),
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_user_id    ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status     ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at DESC);

-- ── Generations ──────────────────────────────────────────────────────────────
-- Every AI artefact (PRDs, roadmaps, architectures, pitch decks, market analyses).

CREATE TABLE IF NOT EXISTS generations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type            TEXT NOT NULL
                    CHECK (type IN ('prd', 'roadmap', 'architecture', 'pitch_deck', 'market_analysis')),
    input_data      JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_content  TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    user_id         UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    project_id      UUID REFERENCES projects(id)   ON DELETE CASCADE,
    workflow_run_id UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_generations_user_id     ON generations(user_id);
CREATE INDEX IF NOT EXISTS idx_generations_project_id  ON generations(project_id);
CREATE INDEX IF NOT EXISTS idx_generations_type        ON generations(type);
CREATE INDEX IF NOT EXISTS idx_generations_created_at  ON generations(created_at DESC);

-- ── Workflow Runs ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS workflow_runs (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_name  TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    input_data     JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_data    JSONB NOT NULL DEFAULT '{}'::jsonb,
    steps          JSONB NOT NULL DEFAULT '[]'::jsonb,
    user_id        UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    project_id     UUID REFERENCES projects(id)   ON DELETE CASCADE,
    error          TEXT,
    started_at     TIMESTAMPTZ,
    completed_at   TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflow_runs_user_id    ON workflow_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_project_id ON workflow_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_status     ON workflow_runs(status);

-- ── Row Level Security ───────────────────────────────────────────────────────

ALTER TABLE users          ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects       ENABLE ROW LEVEL SECURITY;
ALTER TABLE generations    ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_runs  ENABLE ROW LEVEL SECURITY;

-- Users: each row visible/editable only by its owner
DROP POLICY IF EXISTS "users_select_own"  ON users;
DROP POLICY IF EXISTS "users_update_own"  ON users;
DROP POLICY IF EXISTS "users_insert_own"  ON users;
CREATE POLICY "users_select_own"  ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "users_update_own"  ON users FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "users_insert_own"  ON users FOR INSERT WITH CHECK (auth.uid() = id);

-- Projects
DROP POLICY IF EXISTS "projects_select_own" ON projects;
DROP POLICY IF EXISTS "projects_insert_own" ON projects;
DROP POLICY IF EXISTS "projects_update_own" ON projects;
DROP POLICY IF EXISTS "projects_delete_own" ON projects;
CREATE POLICY "projects_select_own" ON projects FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "projects_insert_own" ON projects FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "projects_update_own" ON projects FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "projects_delete_own" ON projects FOR DELETE USING (auth.uid() = user_id);

-- Generations
DROP POLICY IF EXISTS "generations_select_own" ON generations;
DROP POLICY IF EXISTS "generations_insert_own" ON generations;
CREATE POLICY "generations_select_own" ON generations FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "generations_insert_own" ON generations FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Workflow runs
DROP POLICY IF EXISTS "workflow_runs_select_own" ON workflow_runs;
DROP POLICY IF EXISTS "workflow_runs_insert_own" ON workflow_runs;
CREATE POLICY "workflow_runs_select_own" ON workflow_runs FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "workflow_runs_insert_own" ON workflow_runs FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ── Auto-update updated_at ───────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS users_updated_at        ON users;
DROP TRIGGER IF EXISTS projects_updated_at     ON projects;
DROP TRIGGER IF EXISTS generations_updated_at  ON generations;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER generations_updated_at
    BEFORE UPDATE ON generations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
