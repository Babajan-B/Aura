-- AI Learning Coach - Initial Database Schema
-- Phase 3: Database alignment and PGVector setup

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- Table: users
-- User profiles and preferences
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================
-- Table: learning_goals
-- Weekly or active learning goals per user
-- ============================================
CREATE TABLE IF NOT EXISTS learning_goals (
    goal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    goal_text TEXT NOT NULL,
    difficulty_level VARCHAR(50) CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    frequency VARCHAR(50) CHECK (frequency IN ('daily', 'weekly', 'biweekly')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    embedding_vector vector(768)  -- Gemini embedding dimension
);

CREATE INDEX IF NOT EXISTS idx_learning_goals_user_id ON learning_goals(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_goals_is_active ON learning_goals(is_active);
CREATE INDEX IF NOT EXISTS idx_learning_goals_embedding ON learning_goals USING ivfflat (embedding_vector vector_cosine_ops);

-- ============================================
-- Table: sources
-- User selected and system default content sources
-- ============================================
CREATE TABLE IF NOT EXISTS sources (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,  -- NULL means global default source
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('rss', 'youtube', 'reddit', 'x_api', 'website')),
    value TEXT NOT NULL,  -- URL, channel id, subreddit name, handle, etc
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'disabled', 'error')),
    last_fetched_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sources_user_id ON sources(user_id);
CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status);
CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(source_type);

-- ============================================
-- Table: content_items
-- Cleaned content units suitable for embedding
-- ============================================
CREATE TABLE IF NOT EXISTS content_items (
    content_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    clean_text TEXT NOT NULL,
    original_url TEXT,
    source_type VARCHAR(50),
    published_at TIMESTAMP WITH TIME ZONE,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_content_items_source_id ON content_items(source_id);
CREATE INDEX IF NOT EXISTS idx_content_items_published_at ON content_items(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_content_items_url ON content_items(original_url);

-- ============================================
-- Table: content_embeddings
-- Embeddings for external content
-- ============================================
CREATE TABLE IF NOT EXISTS content_embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL REFERENCES content_items(content_id) ON DELETE CASCADE,
    embedding_vector vector(768),  -- Gemini embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(content_id)  -- One embedding per content item
);

CREATE INDEX IF NOT EXISTS idx_content_embeddings_content_id ON content_embeddings(content_id);
CREATE INDEX IF NOT EXISTS idx_content_embeddings_vector ON content_embeddings USING ivfflat (embedding_vector vector_cosine_ops);

-- ============================================
-- Table: internal_rag_embeddings
-- Embeddings for chunks from masterRAG.md
-- ============================================
CREATE TABLE IF NOT EXISTS internal_rag_embeddings (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_name VARCHAR(255),
    chunk_text TEXT NOT NULL,
    embedding_vector vector(768),  -- Gemini embedding dimension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_internal_rag_section ON internal_rag_embeddings(section_name);
CREATE INDEX IF NOT EXISTS idx_internal_rag_vector ON internal_rag_embeddings USING ivfflat (embedding_vector vector_cosine_ops);

-- ============================================
-- Table: digests
-- Weekly digests generated per user and goal
-- ============================================
CREATE TABLE IF NOT EXISTS digests (
    digest_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    goal_id UUID NOT NULL REFERENCES learning_goals(goal_id) ON DELETE CASCADE,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_items INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_digests_user_id ON digests(user_id);
CREATE INDEX IF NOT EXISTS idx_digests_goal_id ON digests(goal_id);
CREATE INDEX IF NOT EXISTS idx_digests_week_start ON digests(week_start_date DESC);

-- ============================================
-- Table: digest_items
-- Individual entries inside each digest
-- ============================================
CREATE TABLE IF NOT EXISTS digest_items (
    digest_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    digest_id UUID NOT NULL REFERENCES digests(digest_id) ON DELETE CASCADE,
    content_id UUID NOT NULL REFERENCES content_items(content_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    why_it_matters TEXT NOT NULL,
    relevance_score FLOAT,
    source_type VARCHAR(50),
    link_url TEXT
);

CREATE INDEX IF NOT EXISTS idx_digest_items_digest_id ON digest_items(digest_id);
CREATE INDEX IF NOT EXISTS idx_digest_items_content_id ON digest_items(content_id);

-- ============================================
-- Table: feedback
-- User feedback on digest items
-- ============================================
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    digest_item_id UUID NOT NULL REFERENCES digest_items(digest_item_id) ON DELETE CASCADE,
    content_id UUID NOT NULL REFERENCES content_items(content_id) ON DELETE CASCADE,
    feedback_value VARCHAR(50) NOT NULL CHECK (feedback_value IN ('useful', 'not_useful')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_digest_item_id ON feedback(digest_item_id);
CREATE INDEX IF NOT EXISTS idx_feedback_content_id ON feedback(content_id);

-- ============================================
-- Table: system_logs
-- System logs for ingestion, errors, and jobs
-- ============================================
CREATE TABLE IF NOT EXISTS system_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    log_type VARCHAR(50) NOT NULL CHECK (log_type IN ('info', 'warning', 'error')),
    component VARCHAR(100) NOT NULL CHECK (component IN ('ingestion', 'rag', 'email', 'api', 'scheduler')),
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_system_logs_type ON system_logs(log_type);
CREATE INDEX IF NOT EXISTS idx_system_logs_component ON system_logs(component);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at DESC);

-- ============================================
-- Triggers for updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Initial system log
-- ============================================
INSERT INTO system_logs (log_type, component, message)
VALUES ('info', 'api', 'Database schema initialized successfully');
