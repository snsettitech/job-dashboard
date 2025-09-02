-- User Service Migration 001: Initial Schema
-- Creates the core users table with authentication and basic profile fields

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Account status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_premium BOOLEAN DEFAULT FALSE,
    
    -- Profile information
    avatar_url VARCHAR(500),
    bio TEXT,
    current_title VARCHAR(255),
    experience_years INTEGER DEFAULT 0,
    education_level VARCHAR(100),
    current_role_level VARCHAR(50), -- entry/mid/senior/executive
    
    -- Contact information
    phone VARCHAR(20),
    location VARCHAR(255),
    timezone VARCHAR(50),
    
    -- Preferences
    preferred_salary_min INTEGER,
    preferred_salary_max INTEGER,
    preferred_locations JSONB, -- Array of location strings
    preferred_remote_option BOOLEAN DEFAULT TRUE,
    preferred_company_sizes JSONB, -- Array of company size preferences
    preferred_industries JSONB, -- Array of industry preferences
    
    -- Account management
    subscription_tier VARCHAR(50) DEFAULT 'basic', -- basic/premium/enterprise
    subscription_status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON users(subscription_status);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE users IS 'Core user accounts with authentication and basic profile information';
COMMENT ON COLUMN users.id IS 'Unique UUID identifier for the user';
COMMENT ON COLUMN users.email IS 'User email address, must be unique';
COMMENT ON COLUMN users.username IS 'Optional username for display purposes';
COMMENT ON COLUMN users.password_hash IS 'Encrypted password hash using bcrypt or similar';
COMMENT ON COLUMN users.is_active IS 'Whether the user account is active';
COMMENT ON COLUMN users.is_verified IS 'Whether the user email has been verified';
COMMENT ON COLUMN users.is_premium IS 'Whether the user has premium subscription';
COMMENT ON COLUMN users.preferred_locations IS 'JSON array of preferred job locations';
COMMENT ON COLUMN users.preferred_company_sizes IS 'JSON array of preferred company sizes';
COMMENT ON COLUMN users.preferred_industries IS 'JSON array of preferred industries';
COMMENT ON COLUMN users.subscription_tier IS 'User subscription level: basic, premium, enterprise';
COMMENT ON COLUMN users.subscription_status IS 'Subscription status: active, suspended, cancelled';

-- Insert initial admin user (password: admin123 - change in production!)
-- INSERT INTO users (email, username, full_name, password_hash, is_verified, is_premium, subscription_tier)
-- VALUES (
--     'admin@jobdashboard.com',
--     'admin',
--     'System Administrator',
--     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5u.Gi', -- admin123
--     TRUE,
--     TRUE,
--     'enterprise'
-- );

