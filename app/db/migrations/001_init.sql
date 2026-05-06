-- ============================================================
--  RAG Pipeline Template – Initial Schema
--  Run once against your Supabase database.
--  Supabase has pgvector pre-installed; the first line is
--  a no-op if the extension already exists.
-- ============================================================

-- 1. Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Documents table
--    Each row is one chunk (a section of a source document).
CREATE TABLE IF NOT EXISTS documents (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    title        TEXT        NOT NULL,
    content      TEXT        NOT NULL,
    source       TEXT,                          -- e.g. filename, URL
    metadata     JSONB       NOT NULL DEFAULT '{}'::jsonb,
    embedding    vector(384) NOT NULL,          -- all-MiniLM-L6-v2 → 384 dims
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. HNSW index for fast approximate nearest-neighbour search
--    m=16 and ef_construction=64 are solid production defaults.
--    Increase ef_construction (e.g. 128) for higher recall at index-build cost.
CREATE INDEX IF NOT EXISTS documents_embedding_hnsw_idx
    ON documents
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- 4. Utility indexes
CREATE INDEX IF NOT EXISTS documents_source_idx  ON documents (source);
CREATE INDEX IF NOT EXISTS documents_created_idx ON documents (created_at DESC);
CREATE INDEX IF NOT EXISTS documents_metadata_idx ON documents USING gin (metadata);

-- 5. Auto-update updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS documents_updated_at ON documents;
CREATE TRIGGER documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- 6. Convenience view for search results (strips the raw vector)
CREATE OR REPLACE VIEW document_search_results AS
SELECT
    id,
    title,
    content,
    source,
    metadata,
    created_at
FROM documents;
