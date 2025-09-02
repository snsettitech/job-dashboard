-- User Service Migration 003: User Preferences and Extended Profiles
-- Creates tables for detailed user profiles and comprehensive preferences

-- Create user_profiles table for extended profile information
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    
    -- Professional information
    linkedin_url VARCHAR(500),
    github_url VARCHAR(500),
    portfolio_url VARCHAR(500),
    website_url VARCHAR(500),
    
    -- Skills and expertise
    skills JSONB, -- Array of skill objects with level
    certifications JSONB, -- Array of certification objects
    languages JSONB, -- Array of language objects with proficiency
    
    -- Work preferences
    work_style VARCHAR(50), -- remote, hybrid, on-site
    availability VARCHAR(50), -- immediate, 2weeks, 1month, 3months
    relocation_willing BOOLEAN DEFAULT FALSE,
    travel_willing BOOLEAN DEFAULT FALSE,
    
    -- Personal information
    date_of_birth DATE,
    gender VARCHAR(20),
    nationality VARCHAR(100),
    work_authorization VARCHAR(100),
    
    -- Privacy settings
    profile_visibility VARCHAR(20) DEFAULT 'public', -- public, private, connections
    contact_visibility VARCHAR(20) DEFAULT 'connections', -- public, connections, private
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create user_preferences table for detailed job search preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    
    -- Job search preferences
    target_titles JSONB, -- Array of desired job titles
    blacklist_titles JSONB, -- Array of titles to avoid
    target_companies JSONB, -- Array of companies of interest
    blacklist_companies JSONB, -- Array of companies to avoid
    
    -- Location preferences
    preferred_locations JSONB, -- Array of location strings
    max_commute_minutes INTEGER,
    remote_preference VARCHAR(20), -- required, preferred, acceptable, never
    relocation_willing BOOLEAN DEFAULT FALSE,
    
    -- Compensation preferences
    salary_expectation_min INTEGER,
    salary_expectation_max INTEGER,
    equity_interest BOOLEAN DEFAULT FALSE,
    benefits_priorities JSONB, -- Array of important benefits
    
    -- Work environment preferences
    company_size_preference JSONB, -- startup, small, medium, large, enterprise
    industry_preferences JSONB, -- Array of preferred industries
    culture_priorities JSONB, -- Array of culture attributes
    work_life_balance_importance INTEGER CHECK (work_life_balance_importance >= 1 AND work_life_balance_importance <= 5), -- 1-5 scale
    
    -- Career goals
    career_stage VARCHAR(50), -- exploring, advancing, transitioning, executive
    skills_to_develop JSONB, -- Skills user wants to learn
    career_timeline VARCHAR(50), -- immediate, 3months, 6months, 1year
    growth_direction VARCHAR(100), -- technical, management, consulting, etc
    
    -- Job search behavior
    application_frequency VARCHAR(20), -- daily, weekly, passive
    auto_apply_enabled BOOLEAN DEFAULT FALSE,
    notification_preferences JSONB, -- Email, SMS, push preferences
    
    -- AI personalization
    matching_algorithm_weights JSONB, -- Custom weights for match factors
    feedback_learning_enabled BOOLEAN DEFAULT TRUE,
    privacy_level VARCHAR(20) DEFAULT 'standard', -- minimal, standard, full
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_work_style ON user_profiles(work_style);
CREATE INDEX IF NOT EXISTS idx_user_profiles_availability ON user_profiles(availability);
CREATE INDEX IF NOT EXISTS idx_user_profiles_profile_visibility ON user_profiles(profile_visibility);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_remote_preference ON user_preferences(remote_preference);
CREATE INDEX IF NOT EXISTS idx_user_preferences_career_stage ON user_preferences(career_stage);
CREATE INDEX IF NOT EXISTS idx_user_preferences_application_frequency ON user_preferences(application_frequency);

-- Create triggers for updated_at
CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON user_profiles 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at 
    BEFORE UPDATE ON user_preferences 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to get comprehensive user profile
CREATE OR REPLACE FUNCTION get_user_profile_complete(user_uuid UUID)
RETURNS TABLE (
    user_id UUID,
    email VARCHAR(255),
    username VARCHAR(100),
    full_name VARCHAR(255),
    is_active BOOLEAN,
    is_verified BOOLEAN,
    is_premium BOOLEAN,
    current_title VARCHAR(255),
    experience_years INTEGER,
    education_level VARCHAR(100),
    current_role_level VARCHAR(50),
    location VARCHAR(255),
    timezone VARCHAR(50),
    linkedin_url VARCHAR(500),
    github_url VARCHAR(500),
    portfolio_url VARCHAR(500),
    skills JSONB,
    certifications JSONB,
    languages JSONB,
    work_style VARCHAR(50),
    availability VARCHAR(50),
    target_titles JSONB,
    preferred_locations JSONB,
    salary_expectation_min INTEGER,
    salary_expectation_max INTEGER,
    company_size_preference JSONB,
    industry_preferences JSONB,
    career_stage VARCHAR(50),
    application_frequency VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id,
        u.email,
        u.username,
        u.full_name,
        u.is_active,
        u.is_verified,
        u.is_premium,
        u.current_title,
        u.experience_years,
        u.education_level,
        u.current_role_level,
        u.location,
        u.timezone,
        up.linkedin_url,
        up.github_url,
        up.portfolio_url,
        up.skills,
        up.certifications,
        up.languages,
        up.work_style,
        up.availability,
        pref.target_titles,
        pref.preferred_locations,
        pref.salary_expectation_min,
        pref.salary_expectation_max,
        pref.company_size_preference,
        pref.industry_preferences,
        pref.career_stage,
        pref.application_frequency
    FROM users u
    LEFT JOIN user_profiles up ON u.id = up.user_id
    LEFT JOIN user_preferences pref ON u.id = pref.user_id
    WHERE u.id = user_uuid;
END;
$$ LANGUAGE plpgsql;

-- Create view for user search optimization
CREATE OR REPLACE VIEW user_search_optimization AS
SELECT 
    u.id as user_id,
    u.email,
    u.full_name,
    u.current_title,
    u.experience_years,
    u.education_level,
    u.current_role_level,
    u.location,
    up.skills,
    up.languages,
    up.work_style,
    up.availability,
    pref.target_titles,
    pref.preferred_locations,
    pref.remote_preference,
    pref.salary_expectation_min,
    pref.salary_expectation_max,
    pref.company_size_preference,
    pref.industry_preferences,
    pref.career_stage,
    pref.application_frequency,
    u.created_at,
    u.last_activity
FROM users u
LEFT JOIN user_profiles up ON u.id = up.user_id
LEFT JOIN user_preferences pref ON u.id = pref.user_id
WHERE u.is_active = TRUE AND u.is_verified = TRUE;

-- Add comments for documentation
COMMENT ON TABLE user_profiles IS 'Extended user profile information for professional networking';
COMMENT ON TABLE user_preferences IS 'Detailed user preferences for job matching and search optimization';

COMMENT ON COLUMN user_profiles.skills IS 'JSON array of skill objects with name, level, and years of experience';
COMMENT ON COLUMN user_profiles.certifications IS 'JSON array of certification objects with name, issuer, and date';
COMMENT ON COLUMN user_profiles.languages IS 'JSON array of language objects with name and proficiency level';
COMMENT ON COLUMN user_profiles.work_style IS 'Preferred work arrangement: remote, hybrid, on-site';
COMMENT ON COLUMN user_profiles.availability IS 'When the user is available to start: immediate, 2weeks, 1month, 3months';
COMMENT ON COLUMN user_profiles.profile_visibility IS 'Who can see the profile: public, private, connections';

COMMENT ON COLUMN user_preferences.target_titles IS 'JSON array of desired job titles for matching';
COMMENT ON COLUMN user_preferences.blacklist_titles IS 'JSON array of job titles to avoid';
COMMENT ON COLUMN user_preferences.target_companies IS 'JSON array of companies of interest';
COMMENT ON COLUMN user_preferences.blacklist_companies IS 'JSON array of companies to avoid';
COMMENT ON COLUMN user_preferences.preferred_locations IS 'JSON array of preferred job locations';
COMMENT ON COLUMN user_preferences.remote_preference IS 'Remote work preference: required, preferred, acceptable, never';
COMMENT ON COLUMN user_preferences.benefits_priorities IS 'JSON array of important benefits: health, dental, 401k, etc';
COMMENT ON COLUMN user_preferences.company_size_preference IS 'JSON array of preferred company sizes';
COMMENT ON COLUMN user_preferences.industry_preferences IS 'JSON array of preferred industries';
COMMENT ON COLUMN user_preferences.culture_priorities IS 'JSON array of culture attributes: collaborative, fast-paced, etc';
COMMENT ON COLUMN user_preferences.work_life_balance_importance IS 'Importance of work-life balance on 1-5 scale';
COMMENT ON COLUMN user_preferences.career_stage IS 'Current career stage: exploring, advancing, transitioning, executive';
COMMENT ON COLUMN user_preferences.skills_to_develop IS 'JSON array of skills the user wants to learn';
COMMENT ON COLUMN user_preferences.career_timeline IS 'Timeline for career change: immediate, 3months, 6months, 1year';
COMMENT ON COLUMN user_preferences.growth_direction IS 'Desired growth direction: technical, management, consulting, etc';
COMMENT ON COLUMN user_preferences.application_frequency IS 'How often user applies: daily, weekly, passive';
COMMENT ON COLUMN user_preferences.notification_preferences IS 'JSON object with email, SMS, push notification settings';
COMMENT ON COLUMN user_preferences.matching_algorithm_weights IS 'JSON object with custom weights for match factors';
COMMENT ON COLUMN user_preferences.feedback_learning_enabled IS 'Whether to use user feedback to improve matching';
COMMENT ON COLUMN user_preferences.privacy_level IS 'Privacy level for data sharing: minimal, standard, full';

COMMENT ON FUNCTION get_user_profile_complete(UUID) IS 'Returns comprehensive user profile with all related data';
COMMENT ON VIEW user_search_optimization IS 'Optimized view for user search and matching algorithms';

