-- AI Service Migration 001: Initial Schema
-- Creates the core AI processing sessions and embeddings tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ai_processing_sessions table for AI processing session tracking
CREATE TABLE IF NOT EXISTS ai_processing_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID, -- References user service (optional for anonymous processing)
    operation_type VARCHAR(50) NOT NULL, -- job_match, resume_optimization, skill_analysis, etc.
    status VARCHAR(20) NOT NULL DEFAULT 'processing', -- processing, completed, failed
    
    -- Session metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    processing_time_ms INTEGER, -- Processing time in milliseconds
    
    -- AI processing metadata
    ai_calls_made INTEGER DEFAULT 0,
    successful_ai_calls INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    model_used VARCHAR(100), -- AI model used (e.g., gpt-4, claude-3, etc.)
    
    -- Error tracking
    error_message TEXT,
    fallback_used BOOLEAN DEFAULT FALSE, -- Whether fallback processing was used
    
    -- Request context
    request_data JSONB, -- Original request data
    response_data JSONB, -- Final response data
    processing_steps JSONB -- Steps taken during processing
);

-- Create embeddings table for vector embeddings storage
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES ai_processing_sessions(id) ON DELETE CASCADE,
    
    -- Embedding metadata
    content_type VARCHAR(50) NOT NULL, -- resume, job_description, skill, etc.
    content_hash VARCHAR(64) NOT NULL, -- Hash of the original content
    content_preview VARCHAR(1000), -- Preview of the content
    
    -- Vector data
    embedding_vector REAL[], -- Vector embedding (requires pgvector extension)
    embedding_dimension INTEGER, -- Dimension of the embedding vector
    model_name VARCHAR(100) NOT NULL, -- Model used for embedding
    
    -- Processing metadata
    processing_time_ms INTEGER, -- Time taken to generate embedding
    tokens_used INTEGER, -- Tokens used for embedding generation
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create ai_models table for tracking AI model usage and performance
CREATE TABLE IF NOT EXISTS ai_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Model information
    model_name VARCHAR(100) UNIQUE NOT NULL,
    model_provider VARCHAR(50) NOT NULL, -- openai, anthropic, google, etc.
    model_version VARCHAR(50),
    model_type VARCHAR(50) NOT NULL, -- text_generation, embedding, classification, etc.
    
    -- Model capabilities
    max_tokens INTEGER,
    context_window INTEGER,
    supported_operations JSONB, -- Array of supported operations
    
    -- Performance metrics
    average_response_time_ms INTEGER,
    success_rate FLOAT,
    cost_per_1k_tokens FLOAT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ai_processing_sessions_session_id ON ai_processing_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_processing_sessions_user_id ON ai_processing_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_processing_sessions_operation_type ON ai_processing_sessions(operation_type);
CREATE INDEX IF NOT EXISTS idx_ai_processing_sessions_status ON ai_processing_sessions(status);
CREATE INDEX IF NOT EXISTS idx_ai_processing_sessions_created_at ON ai_processing_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_processing_sessions_model_used ON ai_processing_sessions(model_used);

CREATE INDEX IF NOT EXISTS idx_embeddings_session_id ON embeddings(session_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_content_type ON embeddings(content_type);
CREATE INDEX IF NOT EXISTS idx_embeddings_content_hash ON embeddings(content_hash);
CREATE INDEX IF NOT EXISTS idx_embeddings_model_name ON embeddings(model_name);
CREATE INDEX IF NOT EXISTS idx_embeddings_created_at ON embeddings(created_at);

CREATE INDEX IF NOT EXISTS idx_ai_models_model_name ON ai_models(model_name);
CREATE INDEX IF NOT EXISTS idx_ai_models_provider ON ai_models(model_provider);
CREATE INDEX IF NOT EXISTS idx_ai_models_type ON ai_models(model_type);
CREATE INDEX IF NOT EXISTS idx_ai_models_is_active ON ai_models(is_active);
CREATE INDEX IF NOT EXISTS idx_ai_models_is_default ON ai_models(is_default);

-- Create updated_at trigger function (if not exists)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
CREATE TRIGGER update_ai_models_updated_at 
    BEFORE UPDATE ON ai_models 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to get processing session statistics
CREATE OR REPLACE FUNCTION get_processing_session_stats(p_user_id UUID DEFAULT NULL)
RETURNS TABLE (
    total_sessions INTEGER,
    successful_sessions INTEGER,
    failed_sessions INTEGER,
    average_processing_time_ms INTEGER,
    total_tokens_used INTEGER,
    most_used_model VARCHAR(100),
    success_rate FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(aps.id)::INTEGER as total_sessions,
        COUNT(CASE WHEN aps.status = 'completed' THEN 1 END)::INTEGER as successful_sessions,
        COUNT(CASE WHEN aps.status = 'failed' THEN 1 END)::INTEGER as failed_sessions,
        AVG(aps.processing_time_ms)::INTEGER as average_processing_time_ms,
        SUM(aps.tokens_used)::INTEGER as total_tokens_used,
        MODE() WITHIN GROUP (ORDER BY aps.model_used) as most_used_model,
        (COUNT(CASE WHEN aps.status = 'completed' THEN 1 END)::FLOAT / COUNT(aps.id)::FLOAT * 100) as success_rate
    FROM ai_processing_sessions aps
    WHERE (p_user_id IS NULL OR aps.user_id = p_user_id);
END;
$$ LANGUAGE plpgsql;

-- Create function to get model performance statistics
CREATE OR REPLACE FUNCTION get_model_performance_stats()
RETURNS TABLE (
    model_name VARCHAR(100),
    total_uses INTEGER,
    success_rate FLOAT,
    average_response_time_ms INTEGER,
    total_tokens_used INTEGER,
    cost_estimate FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        am.model_name,
        COUNT(aps.id)::INTEGER as total_uses,
        (COUNT(CASE WHEN aps.status = 'completed' THEN 1 END)::FLOAT / COUNT(aps.id)::FLOAT * 100) as success_rate,
        AVG(aps.processing_time_ms)::INTEGER as average_response_time_ms,
        SUM(aps.tokens_used)::INTEGER as total_tokens_used,
        (SUM(aps.tokens_used)::FLOAT / 1000) * am.cost_per_1k_tokens as cost_estimate
    FROM ai_models am
    LEFT JOIN ai_processing_sessions aps ON am.model_name = aps.model_used
    WHERE am.is_active = TRUE
    GROUP BY am.model_name, am.cost_per_1k_tokens
    ORDER BY total_uses DESC;
END;
$$ LANGUAGE plpgsql;

-- Create function to get embedding statistics
CREATE OR REPLACE FUNCTION get_embedding_stats(p_session_id UUID DEFAULT NULL)
RETURNS TABLE (
    total_embeddings INTEGER,
    content_types JSONB,
    models_used JSONB,
    average_processing_time_ms INTEGER,
    total_tokens_used INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(e.id)::INTEGER as total_embeddings,
        JSONB_OBJECT_AGG(e.content_type, COUNT(e.id)) as content_types,
        JSONB_OBJECT_AGG(e.model_name, COUNT(e.id)) as models_used,
        AVG(e.processing_time_ms)::INTEGER as average_processing_time_ms,
        SUM(e.tokens_used)::INTEGER as total_tokens_used
    FROM embeddings e
    WHERE (p_session_id IS NULL OR e.session_id = p_session_id);
END;
$$ LANGUAGE plpgsql;

-- Insert default AI models
INSERT INTO ai_models (
    model_name,
    model_provider,
    model_version,
    model_type,
    max_tokens,
    context_window,
    supported_operations,
    average_response_time_ms,
    success_rate,
    cost_per_1k_tokens,
    is_default
) VALUES 
-- OpenAI Models
(
    'gpt-4',
    'openai',
    'gpt-4',
    'text_generation',
    8192,
    8192,
    '["resume_optimization", "job_matching", "skill_analysis", "content_generation"]'::jsonb,
    3000,
    95.5,
    0.03,
    TRUE
),
(
    'gpt-3.5-turbo',
    'openai',
    'gpt-3.5-turbo',
    'text_generation',
    4096,
    4096,
    '["resume_optimization", "job_matching", "skill_analysis", "content_generation"]'::jsonb,
    1500,
    92.0,
    0.002,
    FALSE
),
(
    'text-embedding-ada-002',
    'openai',
    'text-embedding-ada-002',
    'embedding',
    NULL,
    NULL,
    '["text_embedding", "semantic_search"]'::jsonb,
    500,
    98.0,
    0.0001,
    TRUE
),
-- Anthropic Models
(
    'claude-3-opus',
    'anthropic',
    'claude-3-opus-20240229',
    'text_generation',
    4096,
    200000,
    '["resume_optimization", "job_matching", "skill_analysis", "content_generation"]'::jsonb,
    2500,
    96.0,
    0.015,
    FALSE
),
(
    'claude-3-sonnet',
    'anthropic',
    'claude-3-sonnet-20240229',
    'text_generation',
    4096,
    200000,
    '["resume_optimization", "job_matching", "skill_analysis", "content_generation"]'::jsonb,
    2000,
    94.5,
    0.003,
    FALSE
)
ON CONFLICT (model_name) DO UPDATE SET
    model_version = EXCLUDED.model_version,
    average_response_time_ms = EXCLUDED.average_response_time_ms,
    success_rate = EXCLUDED.success_rate,
    cost_per_1k_tokens = EXCLUDED.cost_per_1k_tokens,
    updated_at = CURRENT_TIMESTAMP;

-- Create view for AI processing overview
CREATE OR REPLACE VIEW ai_processing_overview AS
SELECT 
    aps.session_id,
    aps.user_id,
    aps.operation_type,
    aps.status,
    aps.model_used,
    aps.processing_time_ms,
    aps.tokens_used,
    aps.created_at,
    aps.completed_at,
    COUNT(e.id) as embedding_count,
    am.model_provider,
    am.model_type
FROM ai_processing_sessions aps
LEFT JOIN embeddings e ON aps.id = e.session_id
LEFT JOIN ai_models am ON aps.model_used = am.model_name
GROUP BY aps.id, aps.session_id, aps.user_id, aps.operation_type, aps.status, 
         aps.model_used, aps.processing_time_ms, aps.tokens_used, aps.created_at, 
         aps.completed_at, am.model_provider, am.model_type;

-- Add comments for documentation
COMMENT ON TABLE ai_processing_sessions IS 'AI processing session tracking for all AI operations';
COMMENT ON TABLE embeddings IS 'Vector embeddings storage for semantic search and matching';
COMMENT ON TABLE ai_models IS 'AI model configuration and performance tracking';

COMMENT ON COLUMN ai_processing_sessions.session_id IS 'Unique session identifier for tracking';
COMMENT ON COLUMN ai_processing_sessions.user_id IS 'User ID (optional for anonymous processing)';
COMMENT ON COLUMN ai_processing_sessions.operation_type IS 'Type of AI operation: job_match, resume_optimization, skill_analysis, etc.';
COMMENT ON COLUMN ai_processing_sessions.status IS 'Processing status: processing, completed, failed';
COMMENT ON COLUMN ai_processing_sessions.processing_time_ms IS 'Processing time in milliseconds';
COMMENT ON COLUMN ai_processing_sessions.ai_calls_made IS 'Number of AI API calls made';
COMMENT ON COLUMN ai_processing_sessions.successful_ai_calls IS 'Number of successful AI API calls';
COMMENT ON COLUMN ai_processing_sessions.tokens_used IS 'Total tokens used across all AI calls';
COMMENT ON COLUMN ai_processing_sessions.model_used IS 'Primary AI model used for processing';
COMMENT ON COLUMN ai_processing_sessions.error_message IS 'Error message if processing failed';
COMMENT ON COLUMN ai_processing_sessions.fallback_used IS 'Whether fallback processing was used';
COMMENT ON COLUMN ai_processing_sessions.request_data IS 'Original request data in JSON format';
COMMENT ON COLUMN ai_processing_sessions.response_data IS 'Final response data in JSON format';
COMMENT ON COLUMN ai_processing_sessions.processing_steps IS 'JSON array of processing steps taken';

COMMENT ON COLUMN embeddings.content_type IS 'Type of content: resume, job_description, skill, etc.';
COMMENT ON COLUMN embeddings.content_hash IS 'SHA-256 hash of the original content';
COMMENT ON COLUMN embeddings.content_preview IS 'Preview of the content for identification';
COMMENT ON COLUMN embeddings.embedding_vector IS 'Vector embedding (requires pgvector extension)';
COMMENT ON COLUMN embeddings.embedding_dimension IS 'Dimension of the embedding vector';
COMMENT ON COLUMN embeddings.model_name IS 'AI model used for embedding generation';
COMMENT ON COLUMN embeddings.processing_time_ms IS 'Time taken to generate embedding in milliseconds';
COMMENT ON COLUMN embeddings.tokens_used IS 'Tokens used for embedding generation';

COMMENT ON COLUMN ai_models.model_name IS 'Unique model identifier';
COMMENT ON COLUMN ai_models.model_provider IS 'AI provider: openai, anthropic, google, etc.';
COMMENT ON COLUMN ai_models.model_version IS 'Specific version of the model';
COMMENT ON COLUMN ai_models.model_type IS 'Type of model: text_generation, embedding, classification, etc.';
COMMENT ON COLUMN ai_models.max_tokens IS 'Maximum tokens for text generation models';
COMMENT ON COLUMN ai_models.context_window IS 'Context window size for the model';
COMMENT ON COLUMN ai_models.supported_operations IS 'JSON array of operations this model supports';
COMMENT ON COLUMN ai_models.average_response_time_ms IS 'Average response time in milliseconds';
COMMENT ON COLUMN ai_models.success_rate IS 'Success rate percentage';
COMMENT ON COLUMN ai_models.cost_per_1k_tokens IS 'Cost per 1000 tokens in USD';
COMMENT ON COLUMN ai_models.is_active IS 'Whether this model is available for use';
COMMENT ON COLUMN ai_models.is_default IS 'Whether this is the default model for its type';

COMMENT ON FUNCTION get_processing_session_stats(UUID) IS 'Returns processing session statistics for a user or all users';
COMMENT ON FUNCTION get_model_performance_stats() IS 'Returns performance statistics for all AI models';
COMMENT ON FUNCTION get_embedding_stats(UUID) IS 'Returns embedding statistics for a session or all sessions';
COMMENT ON VIEW ai_processing_overview IS 'Overview of AI processing sessions with related data';

