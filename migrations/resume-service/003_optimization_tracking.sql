-- Resume Service Migration 003: Optimization Tracking
-- Creates tables for resume optimization history and analysis results

-- Create resume_optimizations table for optimization attempts and results
CREATE TABLE IF NOT EXISTS resume_optimizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    
    -- Optimization target
    target_job_title VARCHAR(255),
    target_company VARCHAR(255),
    target_industry VARCHAR(100),
    job_description TEXT,
    
    -- Optimization results
    optimized_content TEXT,
    improvements_made JSONB, -- List of specific improvements
    keywords_added JSONB, -- Keywords added for ATS
    keywords_removed JSONB, -- Keywords removed
    
    -- Scoring
    ats_score_before FLOAT,
    ats_score_after FLOAT,
    match_score FLOAT,
    confidence_score FLOAT,
    
    -- Processing metadata
    optimization_model VARCHAR(100), -- AI model used
    processing_time FLOAT, -- Seconds taken
    tokens_used INTEGER,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    error_message TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create resume_analyses table for detailed resume analysis results
CREATE TABLE IF NOT EXISTS resume_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    
    -- Analysis type and scope
    analysis_type VARCHAR(50) NOT NULL, -- skills_analysis, experience_analysis, education_analysis, overall_assessment
    analysis_scope VARCHAR(50), -- full_resume, specific_section, targeted_optimization
    
    -- Analysis results
    analysis_results JSONB, -- Detailed analysis results
    recommendations JSONB, -- Array of improvement recommendations
    strengths JSONB, -- Identified strengths
    weaknesses JSONB, -- Identified weaknesses
    opportunities JSONB, -- Opportunities for improvement
    
    -- Scoring and metrics
    overall_score FLOAT,
    section_scores JSONB, -- Scores for different sections
    confidence_level VARCHAR(20), -- Very High, High, Medium, Low
    
    -- Processing metadata
    analysis_model VARCHAR(100), -- AI model used
    processing_time FLOAT, -- Seconds taken
    tokens_used INTEGER,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    error_message TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create optimization_feedback table for user feedback on optimizations
CREATE TABLE IF NOT EXISTS optimization_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    optimization_id UUID NOT NULL REFERENCES resume_optimizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL, -- References user service
    
    -- Feedback details
    feedback_type VARCHAR(50) NOT NULL, -- positive, negative, neutral, suggestion
    feedback_text TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5), -- 1-5 rating
    
    -- Specific feedback areas
    content_quality_rating INTEGER CHECK (content_quality_rating >= 1 AND content_quality_rating <= 5),
    relevance_rating INTEGER CHECK (relevance_rating >= 1 AND relevance_rating <= 5),
    readability_rating INTEGER CHECK (readability_rating >= 1 AND readability_rating <= 5),
    
    -- User actions
    applied_changes BOOLEAN DEFAULT FALSE, -- Whether user applied the optimization
    applied_changes_description TEXT, -- Description of what was applied
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_resume_optimizations_resume_id ON resume_optimizations(resume_id);
CREATE INDEX IF NOT EXISTS idx_resume_optimizations_status ON resume_optimizations(status);
CREATE INDEX IF NOT EXISTS idx_resume_optimizations_created ON resume_optimizations(created_at);
CREATE INDEX IF NOT EXISTS idx_resume_optimizations_target_job ON resume_optimizations(target_job_title);
CREATE INDEX IF NOT EXISTS idx_resume_optimizations_target_company ON resume_optimizations(target_company);
CREATE INDEX IF NOT EXISTS idx_resume_optimizations_ats_score_after ON resume_optimizations(ats_score_after);

CREATE INDEX IF NOT EXISTS idx_resume_analyses_resume_id ON resume_analyses(resume_id);
CREATE INDEX IF NOT EXISTS idx_resume_analyses_type ON resume_analyses(analysis_type);
CREATE INDEX IF NOT EXISTS idx_resume_analyses_status ON resume_analyses(status);
CREATE INDEX IF NOT EXISTS idx_resume_analyses_created ON resume_analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_resume_analyses_overall_score ON resume_analyses(overall_score);

CREATE INDEX IF NOT EXISTS idx_optimization_feedback_optimization_id ON optimization_feedback(optimization_id);
CREATE INDEX IF NOT EXISTS idx_optimization_feedback_user_id ON optimization_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_optimization_feedback_type ON optimization_feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_optimization_feedback_rating ON optimization_feedback(rating);
CREATE INDEX IF NOT EXISTS idx_optimization_feedback_created ON optimization_feedback(created_at);

-- Create function to get optimization statistics
CREATE OR REPLACE FUNCTION get_optimization_statistics(p_user_id UUID)
RETURNS TABLE (
    total_optimizations INTEGER,
    successful_optimizations INTEGER,
    average_ats_improvement FLOAT,
    average_processing_time FLOAT,
    most_optimized_job_title VARCHAR(255),
    optimization_success_rate FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(ro.id)::INTEGER as total_optimizations,
        COUNT(CASE WHEN ro.status = 'completed' THEN 1 END)::INTEGER as successful_optimizations,
        AVG(ro.ats_score_after - ro.ats_score_before) as average_ats_improvement,
        AVG(ro.processing_time) as average_processing_time,
        MODE() WITHIN GROUP (ORDER BY ro.target_job_title) as most_optimized_job_title,
        (COUNT(CASE WHEN ro.status = 'completed' THEN 1 END)::FLOAT / COUNT(ro.id)::FLOAT * 100) as optimization_success_rate
    FROM resume_optimizations ro
    JOIN resumes r ON ro.resume_id = r.id
    WHERE r.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to get optimization history
CREATE OR REPLACE FUNCTION get_optimization_history(p_resume_id UUID)
RETURNS TABLE (
    optimization_id UUID,
    target_job_title VARCHAR(255),
    target_company VARCHAR(255),
    ats_score_before FLOAT,
    ats_score_after FLOAT,
    match_score FLOAT,
    confidence_score FLOAT,
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    feedback_count INTEGER,
    average_rating FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ro.id,
        ro.target_job_title,
        ro.target_company,
        ro.ats_score_before,
        ro.ats_score_after,
        ro.match_score,
        ro.confidence_score,
        ro.status,
        ro.created_at,
        ro.completed_at,
        COUNT(of.id)::INTEGER as feedback_count,
        AVG(of.rating) as average_rating
    FROM resume_optimizations ro
    LEFT JOIN optimization_feedback of ON ro.id = of.optimization_id
    WHERE ro.resume_id = p_resume_id
    GROUP BY ro.id, ro.target_job_title, ro.target_company, ro.ats_score_before, 
             ro.ats_score_after, ro.match_score, ro.confidence_score, ro.status, 
             ro.created_at, ro.completed_at
    ORDER BY ro.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Create function to get analysis summary
CREATE OR REPLACE FUNCTION get_analysis_summary(p_resume_id UUID)
RETURNS TABLE (
    analysis_id UUID,
    analysis_type VARCHAR(50),
    overall_score FLOAT,
    confidence_level VARCHAR(20),
    recommendations_count INTEGER,
    strengths_count INTEGER,
    weaknesses_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ra.id,
        ra.analysis_type,
        ra.overall_score,
        ra.confidence_level,
        JSONB_ARRAY_LENGTH(ra.recommendations)::INTEGER as recommendations_count,
        JSONB_ARRAY_LENGTH(ra.strengths)::INTEGER as strengths_count,
        JSONB_ARRAY_LENGTH(ra.weaknesses)::INTEGER as weaknesses_count,
        ra.created_at
    FROM resume_analyses ra
    WHERE ra.resume_id = p_resume_id AND ra.status = 'completed'
    ORDER BY ra.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Create view for optimization performance metrics
CREATE OR REPLACE VIEW optimization_performance_metrics AS
SELECT 
    r.user_id,
    COUNT(ro.id) as total_optimizations,
    COUNT(CASE WHEN ro.status = 'completed' THEN 1 END) as successful_optimizations,
    COUNT(CASE WHEN ro.status = 'failed' THEN 1 END) as failed_optimizations,
    AVG(ro.ats_score_after - ro.ats_score_before) as avg_ats_improvement,
    AVG(ro.processing_time) as avg_processing_time,
    AVG(ro.match_score) as avg_match_score,
    AVG(ro.confidence_score) as avg_confidence_score,
    MAX(ro.created_at) as last_optimization_date
FROM resumes r
LEFT JOIN resume_optimizations ro ON r.id = ro.resume_id
GROUP BY r.user_id;

-- Create view for analysis performance metrics
CREATE OR REPLACE VIEW analysis_performance_metrics AS
SELECT 
    r.user_id,
    COUNT(ra.id) as total_analyses,
    COUNT(CASE WHEN ra.status = 'completed' THEN 1 END) as successful_analyses,
    COUNT(CASE WHEN ra.status = 'failed' THEN 1 END) as failed_analyses,
    AVG(ra.overall_score) as avg_overall_score,
    AVG(ra.processing_time) as avg_processing_time,
    MODE() WITHIN GROUP (ORDER BY ra.confidence_level) as most_common_confidence_level,
    MAX(ra.created_at) as last_analysis_date
FROM resumes r
LEFT JOIN resume_analyses ra ON r.id = ra.resume_id
GROUP BY r.user_id;

-- Add comments for documentation
COMMENT ON TABLE resume_optimizations IS 'Resume optimization attempts and results tracking';
COMMENT ON TABLE resume_analyses IS 'Detailed resume analysis results and recommendations';
COMMENT ON TABLE optimization_feedback IS 'User feedback on optimization results';

COMMENT ON COLUMN resume_optimizations.target_job_title IS 'Target job title for optimization';
COMMENT ON COLUMN resume_optimizations.target_company IS 'Target company for optimization';
COMMENT ON COLUMN resume_optimizations.target_industry IS 'Target industry for optimization';
COMMENT ON COLUMN resume_optimizations.job_description IS 'Job description used for optimization';
COMMENT ON COLUMN resume_optimizations.optimized_content IS 'Optimized resume content';
COMMENT ON COLUMN resume_optimizations.improvements_made IS 'JSON array of specific improvements made';
COMMENT ON COLUMN resume_optimizations.keywords_added IS 'JSON array of keywords added for ATS';
COMMENT ON COLUMN resume_optimizations.keywords_removed IS 'JSON array of keywords removed';
COMMENT ON COLUMN resume_optimizations.ats_score_before IS 'ATS score before optimization';
COMMENT ON COLUMN resume_optimizations.ats_score_after IS 'ATS score after optimization';
COMMENT ON COLUMN resume_optimizations.match_score IS 'Match score with target job';
COMMENT ON COLUMN resume_optimizations.confidence_score IS 'Confidence score for optimization quality';
COMMENT ON COLUMN resume_optimizations.optimization_model IS 'AI model used for optimization';
COMMENT ON COLUMN resume_optimizations.processing_time IS 'Time taken for optimization in seconds';
COMMENT ON COLUMN resume_optimizations.tokens_used IS 'Number of tokens used in AI processing';
COMMENT ON COLUMN resume_optimizations.status IS 'Optimization status: pending, processing, completed, failed';

COMMENT ON COLUMN resume_analyses.analysis_type IS 'Type of analysis: skills_analysis, experience_analysis, education_analysis, overall_assessment';
COMMENT ON COLUMN resume_analyses.analysis_scope IS 'Scope of analysis: full_resume, specific_section, targeted_optimization';
COMMENT ON COLUMN resume_analyses.analysis_results IS 'JSON object with detailed analysis results';
COMMENT ON COLUMN resume_analyses.recommendations IS 'JSON array of improvement recommendations';
COMMENT ON COLUMN resume_analyses.strengths IS 'JSON array of identified strengths';
COMMENT ON COLUMN resume_analyses.weaknesses IS 'JSON array of identified weaknesses';
COMMENT ON COLUMN resume_analyses.opportunities IS 'JSON array of opportunities for improvement';
COMMENT ON COLUMN resume_analyses.overall_score IS 'Overall analysis score 0-100';
COMMENT ON COLUMN resume_analyses.section_scores IS 'JSON object with scores for different sections';
COMMENT ON COLUMN resume_analyses.confidence_level IS 'Confidence level: Very High, High, Medium, Low';

COMMENT ON COLUMN optimization_feedback.feedback_type IS 'Type of feedback: positive, negative, neutral, suggestion';
COMMENT ON COLUMN optimization_feedback.feedback_text IS 'Detailed feedback text from user';
COMMENT ON COLUMN optimization_feedback.rating IS 'Overall rating 1-5';
COMMENT ON COLUMN optimization_feedback.content_quality_rating IS 'Content quality rating 1-5';
COMMENT ON COLUMN optimization_feedback.relevance_rating IS 'Relevance rating 1-5';
COMMENT ON COLUMN optimization_feedback.readability_rating IS 'Readability rating 1-5';
COMMENT ON COLUMN optimization_feedback.applied_changes IS 'Whether user applied the optimization changes';
COMMENT ON COLUMN optimization_feedback.applied_changes_description IS 'Description of what changes were applied';

COMMENT ON FUNCTION get_optimization_statistics(UUID) IS 'Returns optimization statistics for a user';
COMMENT ON FUNCTION get_optimization_history(UUID) IS 'Returns optimization history for a resume';
COMMENT ON FUNCTION get_analysis_summary(UUID) IS 'Returns analysis summary for a resume';
COMMENT ON VIEW optimization_performance_metrics IS 'Performance metrics view for optimizations';
COMMENT ON VIEW analysis_performance_metrics IS 'Performance metrics view for analyses';

