-- AI Service Migration 003: Optimization History
-- Creates tables for historical optimization data and analytics

-- Create optimization_history table for historical optimization tracking
CREATE TABLE IF NOT EXISTS optimization_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES ai_processing_sessions(id) ON DELETE CASCADE,
    user_id UUID, -- References user service
    
    -- Historical data
    original_content_hash VARCHAR(64) NOT NULL,
    optimized_content_hash VARCHAR(64) NOT NULL,
    target_content_hash VARCHAR(64), -- Job description or target content
    
    -- Optimization metadata
    optimization_type VARCHAR(50) NOT NULL, -- resume_optimization, content_improvement, skill_enhancement, etc.
    optimization_version VARCHAR(20), -- Version of optimization algorithm used
    optimization_parameters JSONB, -- Parameters used for optimization
    
    -- Results tracking
    improvement_metrics JSONB, -- Various improvement metrics
    quality_scores JSONB, -- Quality scores before and after
    performance_metrics JSONB, -- Performance metrics (time, tokens, etc.)
    
    -- User feedback
    user_satisfaction_score INTEGER CHECK (user_satisfaction_score >= 1 AND user_satisfaction_score <= 5),
    user_feedback TEXT,
    applied_changes BOOLEAN DEFAULT FALSE,
    applied_changes_description TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    feedback_received_at TIMESTAMP WITH TIME ZONE
);

-- Create model_performance_history table for tracking model performance over time
CREATE TABLE IF NOT EXISTS model_performance_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    
    -- Performance metrics
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    average_response_time_ms INTEGER,
    average_tokens_used INTEGER,
    total_cost_estimate FLOAT,
    
    -- Quality metrics
    average_quality_score FLOAT,
    user_satisfaction_score FLOAT,
    accuracy_score FLOAT,
    
    -- Time period
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create user_optimization_preferences table for learning user preferences
CREATE TABLE IF NOT EXISTS user_optimization_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL, -- References user service
    
    -- Preference data
    preferred_optimization_style JSONB, -- User's preferred optimization approach
    preferred_content_tone JSONB, -- Preferred tone and style
    optimization_goals JSONB, -- User's optimization goals
    feedback_patterns JSONB, -- Patterns in user feedback
    
    -- Learning data
    successful_optimizations JSONB, -- Characteristics of successful optimizations
    rejected_optimizations JSONB, -- Characteristics of rejected optimizations
    improvement_areas JSONB, -- Areas where user wants improvements
    
    -- Personalization
    personalization_weights JSONB, -- Weights for different optimization factors
    learning_enabled BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create optimization_templates table for reusable optimization patterns
CREATE TABLE IF NOT EXISTS optimization_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Template information
    template_name VARCHAR(255) NOT NULL,
    template_description TEXT,
    template_category VARCHAR(100), -- resume, cover_letter, profile, etc.
    
    -- Template configuration
    optimization_rules JSONB, -- Rules and guidelines for optimization
    target_metrics JSONB, -- Target metrics for optimization
    quality_criteria JSONB, -- Quality criteria for validation
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    success_rate FLOAT,
    average_improvement_score FLOAT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(100), -- user_id or system
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_optimization_history_session_id ON optimization_history(session_id);
CREATE INDEX IF NOT EXISTS idx_optimization_history_user_id ON optimization_history(user_id);
CREATE INDEX IF NOT EXISTS idx_optimization_history_type ON optimization_history(optimization_type);
CREATE INDEX IF NOT EXISTS idx_optimization_history_created ON optimization_history(created_at);
CREATE INDEX IF NOT EXISTS idx_optimization_history_satisfaction ON optimization_history(user_satisfaction_score);

CREATE INDEX IF NOT EXISTS idx_model_performance_history_model ON model_performance_history(model_name);
CREATE INDEX IF NOT EXISTS idx_model_performance_history_operation ON model_performance_history(operation_type);
CREATE INDEX IF NOT EXISTS idx_model_performance_history_period ON model_performance_history(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_model_performance_history_success_rate ON model_performance_history(successful_requests, total_requests);

CREATE INDEX IF NOT EXISTS idx_user_optimization_preferences_user_id ON user_optimization_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_optimization_preferences_learning ON user_optimization_preferences(learning_enabled);

CREATE INDEX IF NOT EXISTS idx_optimization_templates_category ON optimization_templates(template_category);
CREATE INDEX IF NOT EXISTS idx_optimization_templates_active ON optimization_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_optimization_templates_public ON optimization_templates(is_public);
CREATE INDEX IF NOT EXISTS idx_optimization_templates_success_rate ON optimization_templates(success_rate);

-- Create triggers for updated_at
CREATE TRIGGER update_user_optimization_preferences_updated_at 
    BEFORE UPDATE ON user_optimization_preferences 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_optimization_templates_updated_at 
    BEFORE UPDATE ON optimization_templates 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to get optimization history statistics
CREATE OR REPLACE FUNCTION get_optimization_history_stats(p_user_id UUID DEFAULT NULL, p_days INTEGER DEFAULT 30)
RETURNS TABLE (
    total_optimizations INTEGER,
    average_satisfaction_score FLOAT,
    improvement_rate FLOAT,
    most_common_type VARCHAR(50),
    average_improvement_score FLOAT,
    applied_changes_rate FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(oh.id)::INTEGER as total_optimizations,
        AVG(oh.user_satisfaction_score) as average_satisfaction_score,
        (COUNT(CASE WHEN oh.user_satisfaction_score >= 4 THEN 1 END)::FLOAT / COUNT(oh.id)::FLOAT * 100) as improvement_rate,
        MODE() WITHIN GROUP (ORDER BY oh.optimization_type) as most_common_type,
        AVG((oh.improvement_metrics->>'overall_improvement')::FLOAT) as average_improvement_score,
        (COUNT(CASE WHEN oh.applied_changes = TRUE THEN 1 END)::FLOAT / COUNT(oh.id)::FLOAT * 100) as applied_changes_rate
    FROM optimization_history oh
    WHERE (p_user_id IS NULL OR oh.user_id = p_user_id)
    AND oh.created_at >= CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days;
END;
$$ LANGUAGE plpgsql;

-- Create function to get model performance trends
CREATE OR REPLACE FUNCTION get_model_performance_trends(p_days INTEGER DEFAULT 30)
RETURNS TABLE (
    model_name VARCHAR(100),
    operation_type VARCHAR(50),
    total_requests INTEGER,
    success_rate FLOAT,
    average_response_time_ms INTEGER,
    average_tokens_used INTEGER,
    total_cost_estimate FLOAT,
    average_quality_score FLOAT,
    user_satisfaction_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mph.model_name,
        mph.operation_type,
        SUM(mph.total_requests)::INTEGER as total_requests,
        (SUM(mph.successful_requests)::FLOAT / SUM(mph.total_requests)::FLOAT * 100) as success_rate,
        AVG(mph.average_response_time_ms)::INTEGER as average_response_time_ms,
        AVG(mph.average_tokens_used)::INTEGER as average_tokens_used,
        SUM(mph.total_cost_estimate) as total_cost_estimate,
        AVG(mph.average_quality_score) as average_quality_score,
        AVG(mph.user_satisfaction_score) as user_satisfaction_score
    FROM model_performance_history mph
    WHERE mph.period_start >= CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days
    GROUP BY mph.model_name, mph.operation_type
    ORDER BY total_requests DESC;
END;
$$ LANGUAGE plpgsql;

-- Create function to get user optimization insights
CREATE OR REPLACE FUNCTION get_user_optimization_insights(p_user_id UUID)
RETURNS TABLE (
    preferred_optimization_style JSONB,
    successful_patterns JSONB,
    improvement_areas JSONB,
    optimization_frequency INTEGER,
    average_satisfaction FLOAT,
    most_improved_areas JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        uop.preferred_optimization_style,
        uop.successful_optimizations,
        uop.improvement_areas,
        COUNT(oh.id)::INTEGER as optimization_frequency,
        AVG(oh.user_satisfaction_score) as average_satisfaction,
        JSONB_OBJECT_AGG(
            oh.optimization_type, 
            COUNT(oh.id)
        ) as most_improved_areas
    FROM user_optimization_preferences uop
    LEFT JOIN optimization_history oh ON uop.user_id = oh.user_id
    WHERE uop.user_id = p_user_id
    GROUP BY uop.preferred_optimization_style, uop.successful_optimizations, 
             uop.improvement_areas;
END;
$$ LANGUAGE plpgsql;

-- Create view for optimization analytics
CREATE OR REPLACE VIEW optimization_analytics AS
SELECT 
    oh.optimization_type,
    COUNT(oh.id) as total_optimizations,
    AVG(oh.user_satisfaction_score) as avg_satisfaction,
    AVG((oh.improvement_metrics->>'overall_improvement')::FLOAT) as avg_improvement,
    (COUNT(CASE WHEN oh.applied_changes = TRUE THEN 1 END)::FLOAT / COUNT(oh.id)::FLOAT * 100) as applied_rate,
    MODE() WITHIN GROUP (ORDER BY oh.optimization_version) as most_used_version,
    MAX(oh.created_at) as last_optimization
FROM optimization_history oh
GROUP BY oh.optimization_type
ORDER BY total_optimizations DESC;

-- Create view for model performance analytics
CREATE OR REPLACE VIEW model_performance_analytics AS
SELECT 
    mph.model_name,
    mph.operation_type,
    SUM(mph.total_requests) as total_requests,
    SUM(mph.successful_requests) as successful_requests,
    (SUM(mph.successful_requests)::FLOAT / SUM(mph.total_requests)::FLOAT * 100) as success_rate,
    AVG(mph.average_response_time_ms) as avg_response_time_ms,
    AVG(mph.average_tokens_used) as avg_tokens_used,
    SUM(mph.total_cost_estimate) as total_cost_estimate,
    AVG(mph.average_quality_score) as avg_quality_score,
    AVG(mph.user_satisfaction_score) as avg_user_satisfaction
FROM model_performance_history mph
GROUP BY mph.model_name, mph.operation_type
ORDER BY total_requests DESC;

-- Insert default optimization templates
INSERT INTO optimization_templates (
    template_name,
    template_description,
    template_category,
    optimization_rules,
    target_metrics,
    quality_criteria,
    is_public,
    created_by
) VALUES 
-- Resume Optimization Templates
(
    'ATS-Friendly Resume',
    'Optimize resume for Applicant Tracking Systems',
    'resume',
    '{"keyword_matching": true, "format_standardization": true, "section_optimization": true}'::jsonb,
    '{"ats_score": 85, "keyword_density": 0.02, "readability_score": 70}'::jsonb,
    '{"grammar_check": true, "format_consistency": true, "content_relevance": true}'::jsonb,
    TRUE,
    'system'
),
(
    'Executive Resume',
    'High-level executive resume optimization',
    'resume',
    '{"leadership_focus": true, "achievement_highlighting": true, "strategic_positioning": true}'::jsonb,
    '{"leadership_score": 90, "achievement_impact": 85, "strategic_alignment": 80}'::jsonb,
    '{"executive_tone": true, "achievement_quantification": true, "industry_alignment": true}'::jsonb,
    TRUE,
    'system'
),
(
    'Entry-Level Resume',
    'Optimization for entry-level positions',
    'resume',
    '{"skill_emphasis": true, "education_highlighting": true, "project_showcasing": true}'::jsonb,
    '{"skill_relevance": 80, "education_focus": 75, "project_impact": 70}'::jsonb,
    '{"skill_alignment": true, "education_relevance": true, "project_description": true}'::jsonb,
    TRUE,
    'system'
),
-- Content Optimization Templates
(
    'Professional Tone',
    'Optimize content for professional tone and style',
    'content',
    '{"tone_adjustment": true, "professional_language": true, "clarity_improvement": true}'::jsonb,
    '{"professionalism_score": 85, "clarity_score": 80, "tone_consistency": 90}'::jsonb,
    '{"professional_tone": true, "clear_communication": true, "consistent_style": true}'::jsonb,
    TRUE,
    'system'
),
(
    'Technical Content',
    'Optimize technical content for clarity and precision',
    'content',
    '{"technical_accuracy": true, "clarity_improvement": true, "precision_enhancement": true}'::jsonb,
    '{"technical_accuracy": 90, "clarity_score": 85, "precision_score": 88}'::jsonb,
    '{"technical_correctness": true, "clear_explanation": true, "precise_terminology": true}'::jsonb,
    TRUE,
    'system'
)
ON CONFLICT DO NOTHING;

-- Add comments for documentation
COMMENT ON TABLE optimization_history IS 'Historical optimization data for analytics and learning';
COMMENT ON TABLE model_performance_history IS 'Historical model performance data for optimization';
COMMENT ON TABLE user_optimization_preferences IS 'User preferences and learning data for personalization';
COMMENT ON TABLE optimization_templates IS 'Reusable optimization templates and patterns';

COMMENT ON COLUMN optimization_history.original_content_hash IS 'SHA-256 hash of the original content';
COMMENT ON COLUMN optimization_history.optimized_content_hash IS 'SHA-256 hash of the optimized content';
COMMENT ON COLUMN optimization_history.target_content_hash IS 'SHA-256 hash of the target content (job description, etc.)';
COMMENT ON COLUMN optimization_history.optimization_type IS 'Type of optimization performed';
COMMENT ON COLUMN optimization_history.optimization_version IS 'Version of optimization algorithm used';
COMMENT ON COLUMN optimization_history.optimization_parameters IS 'JSON object with optimization parameters';
COMMENT ON COLUMN optimization_history.improvement_metrics IS 'JSON object with various improvement metrics';
COMMENT ON COLUMN optimization_history.quality_scores IS 'JSON object with quality scores before and after';
COMMENT ON COLUMN optimization_history.performance_metrics IS 'JSON object with performance metrics';
COMMENT ON COLUMN optimization_history.user_satisfaction_score IS 'User satisfaction score 1-5';
COMMENT ON COLUMN optimization_history.user_feedback IS 'Detailed user feedback text';
COMMENT ON COLUMN optimization_history.applied_changes IS 'Whether user applied the optimization changes';
COMMENT ON COLUMN optimization_history.applied_changes_description IS 'Description of what changes were applied';

COMMENT ON COLUMN model_performance_history.model_name IS 'Name of the AI model';
COMMENT ON COLUMN model_performance_history.operation_type IS 'Type of operation performed';
COMMENT ON COLUMN model_performance_history.total_requests IS 'Total number of requests in the period';
COMMENT ON COLUMN model_performance_history.successful_requests IS 'Number of successful requests';
COMMENT ON COLUMN model_performance_history.failed_requests IS 'Number of failed requests';
COMMENT ON COLUMN model_performance_history.average_response_time_ms IS 'Average response time in milliseconds';
COMMENT ON COLUMN model_performance_history.average_tokens_used IS 'Average tokens used per request';
COMMENT ON COLUMN model_performance_history.total_cost_estimate IS 'Estimated total cost for the period';
COMMENT ON COLUMN model_performance_history.average_quality_score IS 'Average quality score';
COMMENT ON COLUMN model_performance_history.user_satisfaction_score IS 'Average user satisfaction score';
COMMENT ON COLUMN model_performance_history.accuracy_score IS 'Accuracy score for the model';
COMMENT ON COLUMN model_performance_history.period_start IS 'Start of the performance period';
COMMENT ON COLUMN model_performance_history.period_end IS 'End of the performance period';

COMMENT ON COLUMN user_optimization_preferences.preferred_optimization_style IS 'JSON object with user preferred optimization approach';
COMMENT ON COLUMN user_optimization_preferences.preferred_content_tone IS 'JSON object with preferred tone and style';
COMMENT ON COLUMN user_optimization_preferences.optimization_goals IS 'JSON object with user optimization goals';
COMMENT ON COLUMN user_optimization_preferences.feedback_patterns IS 'JSON object with patterns in user feedback';
COMMENT ON COLUMN user_optimization_preferences.successful_optimizations IS 'JSON object with characteristics of successful optimizations';
COMMENT ON COLUMN user_optimization_preferences.rejected_optimizations IS 'JSON object with characteristics of rejected optimizations';
COMMENT ON COLUMN user_optimization_preferences.improvement_areas IS 'JSON object with areas where user wants improvements';
COMMENT ON COLUMN user_optimization_preferences.personalization_weights IS 'JSON object with weights for different optimization factors';
COMMENT ON COLUMN user_optimization_preferences.learning_enabled IS 'Whether learning from user feedback is enabled';

COMMENT ON COLUMN optimization_templates.template_name IS 'Name of the optimization template';
COMMENT ON COLUMN optimization_templates.template_description IS 'Description of the template';
COMMENT ON COLUMN optimization_templates.template_category IS 'Category of the template: resume, cover_letter, profile, etc.';
COMMENT ON COLUMN optimization_templates.optimization_rules IS 'JSON object with rules and guidelines for optimization';
COMMENT ON COLUMN optimization_templates.target_metrics IS 'JSON object with target metrics for optimization';
COMMENT ON COLUMN optimization_templates.quality_criteria IS 'JSON object with quality criteria for validation';
COMMENT ON COLUMN optimization_templates.usage_count IS 'Number of times this template has been used';
COMMENT ON COLUMN optimization_templates.success_rate IS 'Success rate percentage for this template';
COMMENT ON COLUMN optimization_templates.average_improvement_score IS 'Average improvement score achieved with this template';
COMMENT ON COLUMN optimization_templates.is_active IS 'Whether this template is active';
COMMENT ON COLUMN optimization_templates.is_public IS 'Whether this template is publicly available';
COMMENT ON COLUMN optimization_templates.created_by IS 'User ID or system that created this template';

COMMENT ON FUNCTION get_optimization_history_stats(UUID, INTEGER) IS 'Returns optimization history statistics for a user or all users';
COMMENT ON FUNCTION get_model_performance_trends(INTEGER) IS 'Returns model performance trends over a specified period';
COMMENT ON FUNCTION get_user_optimization_insights(UUID) IS 'Returns optimization insights for a specific user';
COMMENT ON VIEW optimization_analytics IS 'Analytics view for optimization performance';
COMMENT ON VIEW model_performance_analytics IS 'Analytics view for model performance';

