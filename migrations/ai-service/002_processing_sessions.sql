-- AI Service Migration 002: Processing Sessions
-- Creates additional tables for job matching and resume optimization processing

-- Create resume_optimizations table for resume optimization results
CREATE TABLE IF NOT EXISTS resume_optimizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES ai_processing_sessions(id) ON DELETE CASCADE,
    user_id UUID, -- References user service
    
    -- Original content
    original_resume_hash VARCHAR(64) NOT NULL,
    original_resume_preview VARCHAR(1000),
    job_description_hash VARCHAR(64) NOT NULL,
    job_description_preview VARCHAR(1000),
    
    -- Optimization results
    optimized_resume TEXT NOT NULL,
    improvements_made JSONB, -- Array of improvement descriptions
    keywords_added JSONB, -- Array of keywords
    ats_score_improvement VARCHAR(20), -- e.g., "+35%"
    match_score_prediction FLOAT,
    
    -- Quality metrics
    confidence_score FLOAT,
    confidence_level VARCHAR(20), -- Very High, High, Medium, Low
    quality_validation_passed BOOLEAN DEFAULT FALSE,
    
    -- Processing metadata
    model_used VARCHAR(100),
    processing_time_ms INTEGER,
    tokens_used INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create job_match_analyses table for job matching analysis results
CREATE TABLE IF NOT EXISTS job_match_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES ai_processing_sessions(id) ON DELETE CASCADE,
    user_id UUID, -- References user service
    
    -- Job and resume data
    resume_hash VARCHAR(64) NOT NULL,
    resume_preview VARCHAR(1000),
    job_posting_hash VARCHAR(64) NOT NULL,
    job_posting_preview VARCHAR(1000),
    
    -- Analysis results
    match_score FLOAT NOT NULL, -- 0-100 score
    match_breakdown JSONB, -- Detailed breakdown of match factors
    skill_match_percentage FLOAT,
    experience_match_percentage FLOAT,
    education_match_percentage FLOAT,
    
    -- Recommendations
    improvement_suggestions JSONB, -- Array of improvement suggestions
    missing_skills JSONB, -- Array of missing skills
    strengths_highlighted JSONB, -- Array of strengths to highlight
    
    -- Confidence and quality
    confidence_score FLOAT,
    confidence_level VARCHAR(20), -- Very High, High, Medium, Low
    analysis_quality_score FLOAT,
    
    -- Processing metadata
    model_used VARCHAR(100),
    processing_time_ms INTEGER,
    tokens_used INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create skill_analyses table for skill analysis results
CREATE TABLE IF NOT EXISTS skill_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES ai_processing_sessions(id) ON DELETE CASCADE,
    user_id UUID, -- References user service
    
    -- Content data
    content_hash VARCHAR(64) NOT NULL,
    content_preview VARCHAR(1000),
    content_type VARCHAR(50) NOT NULL, -- resume, job_description, profile, etc.
    
    -- Analysis results
    identified_skills JSONB, -- Array of identified skills with confidence
    skill_categories JSONB, -- Skills grouped by category
    skill_levels JSONB, -- Skill proficiency levels
    missing_skills JSONB, -- Skills that might be missing
    
    -- Market analysis
    market_demand_analysis JSONB, -- Market demand for identified skills
    skill_trends JSONB, -- Trending skills in the market
    salary_impact_analysis JSONB, -- How skills impact salary
    
    -- Recommendations
    skill_development_suggestions JSONB, -- Skills to develop
    certification_recommendations JSONB, -- Recommended certifications
    learning_paths JSONB, -- Suggested learning paths
    
    -- Processing metadata
    model_used VARCHAR(100),
    processing_time_ms INTEGER,
    tokens_used INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create content_analyses table for general content analysis
CREATE TABLE IF NOT EXISTS content_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES ai_processing_sessions(id) ON DELETE CASCADE,
    user_id UUID, -- References user service
    
    -- Content data
    content_hash VARCHAR(64) NOT NULL,
    content_preview VARCHAR(1000),
    content_type VARCHAR(50) NOT NULL, -- resume, cover_letter, profile, etc.
    
    -- Analysis results
    readability_score FLOAT, -- Readability score
    tone_analysis JSONB, -- Tone and style analysis
    grammar_analysis JSONB, -- Grammar and language analysis
    structure_analysis JSONB, -- Document structure analysis
    
    -- Quality metrics
    overall_quality_score FLOAT,
    completeness_score FLOAT,
    professionalism_score FLOAT,
    
    -- Recommendations
    improvement_suggestions JSONB, -- General improvement suggestions
    style_recommendations JSONB, -- Style and tone recommendations
    structure_recommendations JSONB, -- Structure recommendations
    
    -- Processing metadata
    model_used VARCHAR(100),
    processing_time_ms INTEGER,
    tokens_used INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_resume_optimizations_session_id ON resume_optimizations(session_id);
CREATE INDEX IF NOT EXISTS idx_resume_optimizations_user_id ON resume_optimizations(user_id);
CREATE INDEX IF NOT EXISTS idx_resume_optimizations_original_hash ON resume_optimizations(original_resume_hash);
CREATE INDEX IF NOT EXISTS idx_resume_optimizations_job_hash ON resume_optimizations(job_description_hash);
CREATE INDEX IF NOT EXISTS idx_resume_optimizations_confidence ON resume_optimizations(confidence_score);
CREATE INDEX IF NOT EXISTS idx_resume_optimizations_quality ON resume_optimizations(quality_validation_passed);
CREATE INDEX IF NOT EXISTS idx_resume_optimizations_created ON resume_optimizations(created_at);

CREATE INDEX IF NOT EXISTS idx_job_match_analyses_session_id ON job_match_analyses(session_id);
CREATE INDEX IF NOT EXISTS idx_job_match_analyses_user_id ON job_match_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_job_match_analyses_resume_hash ON job_match_analyses(resume_hash);
CREATE INDEX IF NOT EXISTS idx_job_match_analyses_job_hash ON job_match_analyses(job_posting_hash);
CREATE INDEX IF NOT EXISTS idx_job_match_analyses_match_score ON job_match_analyses(match_score);
CREATE INDEX IF NOT EXISTS idx_job_match_analyses_confidence ON job_match_analyses(confidence_score);
CREATE INDEX IF NOT EXISTS idx_job_match_analyses_created ON job_match_analyses(created_at);

CREATE INDEX IF NOT EXISTS idx_skill_analyses_session_id ON skill_analyses(session_id);
CREATE INDEX IF NOT EXISTS idx_skill_analyses_user_id ON skill_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_skill_analyses_content_hash ON skill_analyses(content_hash);
CREATE INDEX IF NOT EXISTS idx_skill_analyses_content_type ON skill_analyses(content_type);
CREATE INDEX IF NOT EXISTS idx_skill_analyses_created ON skill_analyses(created_at);

CREATE INDEX IF NOT EXISTS idx_content_analyses_session_id ON content_analyses(session_id);
CREATE INDEX IF NOT EXISTS idx_content_analyses_user_id ON content_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_content_analyses_content_hash ON content_analyses(content_hash);
CREATE INDEX IF NOT EXISTS idx_content_analyses_content_type ON content_analyses(content_type);
CREATE INDEX IF NOT EXISTS idx_content_analyses_quality_score ON content_analyses(overall_quality_score);
CREATE INDEX IF NOT EXISTS idx_content_analyses_created ON content_analyses(created_at);

-- Create function to get optimization statistics
CREATE OR REPLACE FUNCTION get_optimization_statistics(p_user_id UUID DEFAULT NULL)
RETURNS TABLE (
    total_optimizations INTEGER,
    successful_optimizations INTEGER,
    average_confidence_score FLOAT,
    average_ats_improvement VARCHAR(20),
    average_processing_time_ms INTEGER,
    most_used_model VARCHAR(100),
    quality_validation_rate FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(ro.id)::INTEGER as total_optimizations,
        COUNT(CASE WHEN ro.quality_validation_passed = TRUE THEN 1 END)::INTEGER as successful_optimizations,
        AVG(ro.confidence_score) as average_confidence_score,
        MODE() WITHIN GROUP (ORDER BY ro.ats_score_improvement) as average_ats_improvement,
        AVG(ro.processing_time_ms)::INTEGER as average_processing_time_ms,
        MODE() WITHIN GROUP (ORDER BY ro.model_used) as most_used_model,
        (COUNT(CASE WHEN ro.quality_validation_passed = TRUE THEN 1 END)::FLOAT / COUNT(ro.id)::FLOAT * 100) as quality_validation_rate
    FROM resume_optimizations ro
    WHERE (p_user_id IS NULL OR ro.user_id = p_user_id);
END;
$$ LANGUAGE plpgsql;

-- Create function to get job matching statistics
CREATE OR REPLACE FUNCTION get_job_matching_statistics(p_user_id UUID DEFAULT NULL)
RETURNS TABLE (
    total_analyses INTEGER,
    average_match_score FLOAT,
    average_confidence_score FLOAT,
    average_processing_time_ms INTEGER,
    most_used_model VARCHAR(100),
    high_match_rate FLOAT -- Percentage of matches above 80%
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(jma.id)::INTEGER as total_analyses,
        AVG(jma.match_score) as average_match_score,
        AVG(jma.confidence_score) as average_confidence_score,
        AVG(jma.processing_time_ms)::INTEGER as average_processing_time_ms,
        MODE() WITHIN GROUP (ORDER BY jma.model_used) as most_used_model,
        (COUNT(CASE WHEN jma.match_score >= 80 THEN 1 END)::FLOAT / COUNT(jma.id)::FLOAT * 100) as high_match_rate
    FROM job_match_analyses jma
    WHERE (p_user_id IS NULL OR jma.user_id = p_user_id);
END;
$$ LANGUAGE plpgsql;

-- Create function to get skill analysis statistics
CREATE OR REPLACE FUNCTION get_skill_analysis_statistics(p_user_id UUID DEFAULT NULL)
RETURNS TABLE (
    total_analyses INTEGER,
    average_skills_identified INTEGER,
    most_analyzed_content_type VARCHAR(50),
    average_processing_time_ms INTEGER,
    most_used_model VARCHAR(100)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(sa.id)::INTEGER as total_analyses,
        AVG(JSONB_ARRAY_LENGTH(sa.identified_skills))::INTEGER as average_skills_identified,
        MODE() WITHIN GROUP (ORDER BY sa.content_type) as most_analyzed_content_type,
        AVG(sa.processing_time_ms)::INTEGER as average_processing_time_ms,
        MODE() WITHIN GROUP (ORDER BY sa.model_used) as most_used_model
    FROM skill_analyses sa
    WHERE (p_user_id IS NULL OR sa.user_id = p_user_id);
END;
$$ LANGUAGE plpgsql;

-- Create view for processing session summary
CREATE OR REPLACE VIEW processing_session_summary AS
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
    COUNT(ro.id) as optimization_count,
    COUNT(jma.id) as job_match_count,
    COUNT(sa.id) as skill_analysis_count,
    COUNT(ca.id) as content_analysis_count,
    COUNT(e.id) as embedding_count
FROM ai_processing_sessions aps
LEFT JOIN resume_optimizations ro ON aps.id = ro.session_id
LEFT JOIN job_match_analyses jma ON aps.id = jma.session_id
LEFT JOIN skill_analyses sa ON aps.id = sa.session_id
LEFT JOIN content_analyses ca ON aps.id = ca.session_id
LEFT JOIN embeddings e ON aps.id = e.session_id
GROUP BY aps.id, aps.session_id, aps.user_id, aps.operation_type, aps.status, 
         aps.model_used, aps.processing_time_ms, aps.tokens_used, aps.created_at, aps.completed_at;

-- Create view for user processing activity
CREATE OR REPLACE VIEW user_processing_activity AS
SELECT 
    aps.user_id,
    aps.operation_type,
    COUNT(aps.id) as session_count,
    AVG(aps.processing_time_ms)::INTEGER as avg_processing_time_ms,
    SUM(aps.tokens_used) as total_tokens_used,
    MAX(aps.created_at) as last_activity,
    MODE() WITHIN GROUP (ORDER BY aps.model_used) as most_used_model
FROM ai_processing_sessions aps
WHERE aps.user_id IS NOT NULL
GROUP BY aps.user_id, aps.operation_type
ORDER BY aps.user_id, session_count DESC;

-- Add comments for documentation
COMMENT ON TABLE resume_optimizations IS 'Resume optimization results from AI processing';
COMMENT ON TABLE job_match_analyses IS 'Job matching analysis results from AI processing';
COMMENT ON TABLE skill_analyses IS 'Skill analysis results from AI processing';
COMMENT ON TABLE content_analyses IS 'General content analysis results from AI processing';

COMMENT ON COLUMN resume_optimizations.original_resume_hash IS 'SHA-256 hash of the original resume content';
COMMENT ON COLUMN resume_optimizations.original_resume_preview IS 'Preview of the original resume content';
COMMENT ON COLUMN resume_optimizations.job_description_hash IS 'SHA-256 hash of the job description content';
COMMENT ON COLUMN resume_optimizations.job_description_preview IS 'Preview of the job description content';
COMMENT ON COLUMN resume_optimizations.optimized_resume IS 'Optimized resume content generated by AI';
COMMENT ON COLUMN resume_optimizations.improvements_made IS 'JSON array of specific improvements made';
COMMENT ON COLUMN resume_optimizations.keywords_added IS 'JSON array of keywords added for ATS optimization';
COMMENT ON COLUMN resume_optimizations.ats_score_improvement IS 'Percentage improvement in ATS score (e.g., "+35%")';
COMMENT ON COLUMN resume_optimizations.match_score_prediction IS 'Predicted match score with the job description';
COMMENT ON COLUMN resume_optimizations.confidence_score IS 'Confidence score for the optimization quality';
COMMENT ON COLUMN resume_optimizations.confidence_level IS 'Confidence level: Very High, High, Medium, Low';
COMMENT ON COLUMN resume_optimizations.quality_validation_passed IS 'Whether the optimization passed quality validation';

COMMENT ON COLUMN job_match_analyses.resume_hash IS 'SHA-256 hash of the resume content';
COMMENT ON COLUMN job_match_analyses.resume_preview IS 'Preview of the resume content';
COMMENT ON COLUMN job_match_analyses.job_posting_hash IS 'SHA-256 hash of the job posting content';
COMMENT ON COLUMN job_match_analyses.job_posting_preview IS 'Preview of the job posting content';
COMMENT ON COLUMN job_match_analyses.match_score IS 'Overall match score between resume and job (0-100)';
COMMENT ON COLUMN job_match_analyses.match_breakdown IS 'JSON object with detailed breakdown of match factors';
COMMENT ON COLUMN job_match_analyses.skill_match_percentage IS 'Percentage match in skills';
COMMENT ON COLUMN job_match_analyses.experience_match_percentage IS 'Percentage match in experience';
COMMENT ON COLUMN job_match_analyses.education_match_percentage IS 'Percentage match in education';
COMMENT ON COLUMN job_match_analyses.improvement_suggestions IS 'JSON array of improvement suggestions';
COMMENT ON COLUMN job_match_analyses.missing_skills IS 'JSON array of skills missing from resume';
COMMENT ON COLUMN job_match_analyses.strengths_highlighted IS 'JSON array of strengths to highlight';
COMMENT ON COLUMN job_match_analyses.confidence_score IS 'Confidence score for the analysis';
COMMENT ON COLUMN job_match_analyses.confidence_level IS 'Confidence level: Very High, High, Medium, Low';
COMMENT ON COLUMN job_match_analyses.analysis_quality_score IS 'Quality score for the analysis';

COMMENT ON COLUMN skill_analyses.content_hash IS 'SHA-256 hash of the analyzed content';
COMMENT ON COLUMN skill_analyses.content_preview IS 'Preview of the analyzed content';
COMMENT ON COLUMN skill_analyses.content_type IS 'Type of content: resume, job_description, profile, etc.';
COMMENT ON COLUMN skill_analyses.identified_skills IS 'JSON array of identified skills with confidence scores';
COMMENT ON COLUMN skill_analyses.skill_categories IS 'JSON object with skills grouped by category';
COMMENT ON COLUMN skill_analyses.skill_levels IS 'JSON object with skill proficiency levels';
COMMENT ON COLUMN skill_analyses.missing_skills IS 'JSON array of skills that might be missing';
COMMENT ON COLUMN skill_analyses.market_demand_analysis IS 'JSON object with market demand analysis for skills';
COMMENT ON COLUMN skill_analyses.skill_trends IS 'JSON object with trending skills in the market';
COMMENT ON COLUMN skill_analyses.salary_impact_analysis IS 'JSON object with salary impact analysis';
COMMENT ON COLUMN skill_analyses.skill_development_suggestions IS 'JSON array of skills to develop';
COMMENT ON COLUMN skill_analyses.certification_recommendations IS 'JSON array of recommended certifications';
COMMENT ON COLUMN skill_analyses.learning_paths IS 'JSON array of suggested learning paths';

COMMENT ON COLUMN content_analyses.content_hash IS 'SHA-256 hash of the analyzed content';
COMMENT ON COLUMN content_analyses.content_preview IS 'Preview of the analyzed content';
COMMENT ON COLUMN content_analyses.content_type IS 'Type of content: resume, cover_letter, profile, etc.';
COMMENT ON COLUMN content_analyses.readability_score IS 'Readability score for the content';
COMMENT ON COLUMN content_analyses.tone_analysis IS 'JSON object with tone and style analysis';
COMMENT ON COLUMN content_analyses.grammar_analysis IS 'JSON object with grammar and language analysis';
COMMENT ON COLUMN content_analyses.structure_analysis IS 'JSON object with document structure analysis';
COMMENT ON COLUMN content_analyses.overall_quality_score IS 'Overall quality score for the content';
COMMENT ON COLUMN content_analyses.completeness_score IS 'Completeness score for the content';
COMMENT ON COLUMN content_analyses.professionalism_score IS 'Professionalism score for the content';
COMMENT ON COLUMN content_analyses.improvement_suggestions IS 'JSON array of general improvement suggestions';
COMMENT ON COLUMN content_analyses.style_recommendations IS 'JSON array of style and tone recommendations';
COMMENT ON COLUMN content_analyses.structure_recommendations IS 'JSON array of structure recommendations';

COMMENT ON FUNCTION get_optimization_statistics(UUID) IS 'Returns optimization statistics for a user or all users';
COMMENT ON FUNCTION get_job_matching_statistics(UUID) IS 'Returns job matching statistics for a user or all users';
COMMENT ON FUNCTION get_skill_analysis_statistics(UUID) IS 'Returns skill analysis statistics for a user or all users';
COMMENT ON VIEW processing_session_summary IS 'Summary view of processing sessions with related data';
COMMENT ON VIEW user_processing_activity IS 'User processing activity summary';

