-- Little Lairs v2 — PostgreSQL Schema
-- Version: 2.0.0 | 2026-04-09
-- DO NOT EDIT MANUALLY — use Alembic migrations

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────────────────────────────────
--  FAILURE TAXONOMY
-- ─────────────────────────────────────────────
CREATE TYPE failure_type AS ENUM (
    'SUPPORTED',
    'DEAD_LINK',
    'FABRICATED_URL',
    'IRRELEVANT_SUPPORT',
    'CLAIM_MISMATCH',
    'INDETERMINATE',
    'FORMAT_CORRUPTION',
    'TEMPORAL_MISMATCH',
    'REDIRECT_ABUSE'
);

CREATE TYPE run_status AS ENUM ('queued', 'running', 'completed', 'failed');

CREATE TYPE run_label AS ENUM ('LIAR', 'SLOPPY', 'OK');

-- ─────────────────────────────────────────────
--  BENCHMARKS
-- ─────────────────────────────────────────────
CREATE TABLE benchmarks (
    benchmark_id    SERIAL PRIMARY KEY,
    version         TEXT NOT NULL UNIQUE,           -- e.g. "v1.0.0"
    prompt_hash     TEXT NOT NULL,                  -- SHA256 of all prompt texts
    scoring_rules   JSONB NOT NULL DEFAULT '{}',    -- snapshot of scoring config
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
--  PROMPTS
-- ─────────────────────────────────────────────
CREATE TABLE prompts (
    prompt_id       SERIAL PRIMARY KEY,
    benchmark_id    INT NOT NULL REFERENCES benchmarks(benchmark_id),
    category        TEXT NOT NULL,                  -- A–H
    difficulty      INT NOT NULL DEFAULT 1,
    text            TEXT NOT NULL,
    expected_claims JSONB NOT NULL DEFAULT '[]',
    metadata        JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_prompts_benchmark ON prompts(benchmark_id);
CREATE INDEX idx_prompts_category  ON prompts(category);

-- ─────────────────────────────────────────────
--  MODELS
-- ─────────────────────────────────────────────
CREATE TABLE models (
    model_id        TEXT PRIMARY KEY,               -- e.g. "openai/gpt-4o"
    provider        TEXT NOT NULL,
    display_name    TEXT NOT NULL,
    family          TEXT,
    is_reasoning    BOOLEAN NOT NULL DEFAULT FALSE,
    is_open         BOOLEAN NOT NULL DEFAULT FALSE,
    price_tier      TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
--  RUNS
-- ─────────────────────────────────────────────
CREATE TABLE runs (
    run_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    benchmark_id    INT NOT NULL REFERENCES benchmarks(benchmark_id),
    model_id        TEXT NOT NULL REFERENCES models(model_id),
    status          run_status NOT NULL DEFAULT 'queued',
    temperature     FLOAT NOT NULL DEFAULT 0.0,
    seed            INT,
    max_tokens      INT,
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    artifact_url    TEXT,                           -- S3 or static URL to .json artifact
    raw_responses   JSONB NOT NULL DEFAULT '[]',    -- immutable snapshot
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_runs_model     ON runs(model_id);
CREATE INDEX idx_runs_benchmark ON runs(benchmark_id);
CREATE INDEX idx_runs_status    ON runs(status);

-- ─────────────────────────────────────────────
--  EXTRACTED URLS
-- ─────────────────────────────────────────────
CREATE TABLE extracted_urls (
    url_id          SERIAL PRIMARY KEY,
    run_id          UUID NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    prompt_id       INT NOT NULL REFERENCES prompts(prompt_id),
    url             TEXT NOT NULL,
    context_text    TEXT,                           -- 200-char window around URL in response
    position        INT                             -- char offset in response
);

CREATE INDEX idx_urls_run    ON extracted_urls(run_id);
CREATE INDEX idx_urls_prompt ON extracted_urls(prompt_id);
CREATE INDEX idx_urls_url    ON extracted_urls(url);

-- ─────────────────────────────────────────────
--  URL VERIFICATIONS
-- ─────────────────────────────────────────────
CREATE TABLE url_verifications (
    ver_id          SERIAL PRIMARY KEY,
    url_id          INT NOT NULL REFERENCES extracted_urls(url_id) ON DELETE CASCADE,
    http_status     INT,                            -- e.g. 200, 404, NULL if DNS fail
    final_url       TEXT,                           -- after redirects
    failure_type    failure_type NOT NULL,
    page_title      TEXT,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cached_path     TEXT,
    confidence      FLOAT NOT NULL DEFAULT 1.0,
    metadata        JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_ver_url          ON url_verifications(url_id);
CREATE INDEX idx_ver_failure_type ON url_verifications(failure_type);

-- ─────────────────────────────────────────────
--  ADJUDICATIONS
-- ─────────────────────────────────────────────
CREATE TABLE adjudications (
    adj_id          SERIAL PRIMARY KEY,
    url_id          INT NOT NULL REFERENCES extracted_urls(url_id) ON DELETE CASCADE,
    prompt_id       INT NOT NULL REFERENCES prompts(prompt_id),
    claim_text      TEXT NOT NULL,
    verdict         failure_type NOT NULL,
    evidence_snippet TEXT,
    confidence      FLOAT NOT NULL DEFAULT 1.0,
    adjudicated_by  TEXT NOT NULL DEFAULT 'auto',   -- 'auto' or reviewer name
    metadata        JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_adj_url    ON adjudications(url_id);
CREATE INDEX idx_adj_prompt ON adjudications(prompt_id);

-- ─────────────────────────────────────────────
--  RUN SCORES
-- ─────────────────────────────────────────────
CREATE TABLE run_scores (
    score_id        SERIAL PRIMARY KEY,
    run_id          UUID NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    score           INT NOT NULL,                   -- 0–100
    fabricated_count INT NOT NULL DEFAULT 0,
    dead_count      INT NOT NULL DEFAULT 0,
    total_anchors   INT NOT NULL DEFAULT 0,
    label           run_label NOT NULL,
    breakdown       JSONB NOT NULL DEFAULT '{}',    -- per-prompt breakdown
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_scores_run ON run_scores(run_id);
