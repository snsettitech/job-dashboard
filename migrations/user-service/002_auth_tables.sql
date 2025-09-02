-- User Service Migration 002: Authentication Tables
-- Creates tables for user sessions, refresh tokens, password resets, and email verifications

-- Create user_sessions table for tracking active sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(500) UNIQUE NOT NULL,
    
    -- Session information
    ip_address VARCHAR(45), -- IPv6 compatible
    user_agent TEXT,
    device_type VARCHAR(50), -- mobile, tablet, desktop
    browser VARCHAR(100),
    os VARCHAR(100),
    
    -- Session status
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create refresh_tokens table for JWT refresh tokens
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    
    -- Token information
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE,
    
    -- Security information
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Create password_resets table for password reset tokens
CREATE TABLE IF NOT EXISTS password_resets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    
    -- Token information
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP WITH TIME ZONE,
    
    -- Security information
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Create email_verifications table for email verification tokens
CREATE TABLE IF NOT EXISTS email_verifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    
    -- Token information
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance and security
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_is_revoked ON refresh_tokens(is_revoked);

CREATE INDEX IF NOT EXISTS idx_password_resets_user_id ON password_resets(user_id);
CREATE INDEX IF NOT EXISTS idx_password_resets_token ON password_resets(token);
CREATE INDEX IF NOT EXISTS idx_password_resets_expires_at ON password_resets(expires_at);
CREATE INDEX IF NOT EXISTS idx_password_resets_is_used ON password_resets(is_used);

CREATE INDEX IF NOT EXISTS idx_email_verifications_user_id ON email_verifications(user_id);
CREATE INDEX IF NOT EXISTS idx_email_verifications_token ON email_verifications(token);
CREATE INDEX IF NOT EXISTS idx_email_verifications_expires_at ON email_verifications(expires_at);
CREATE INDEX IF NOT EXISTS idx_email_verifications_is_used ON email_verifications(is_used);

-- Create trigger for last_activity update on user_sessions
CREATE TRIGGER update_user_sessions_last_activity 
    BEFORE UPDATE ON user_sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to clean up expired sessions and tokens
CREATE OR REPLACE FUNCTION cleanup_expired_auth_data()
RETURNS void AS $$
BEGIN
    -- Clean up expired sessions
    DELETE FROM user_sessions 
    WHERE expires_at < CURRENT_TIMESTAMP OR is_active = FALSE;
    
    -- Clean up expired refresh tokens
    DELETE FROM refresh_tokens 
    WHERE expires_at < CURRENT_TIMESTAMP OR is_revoked = TRUE;
    
    -- Clean up expired password resets
    DELETE FROM password_resets 
    WHERE expires_at < CURRENT_TIMESTAMP OR is_used = TRUE;
    
    -- Clean up expired email verifications
    DELETE FROM email_verifications 
    WHERE expires_at < CURRENT_TIMESTAMP OR is_used = TRUE;
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to clean up expired data (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-expired-auth', '0 2 * * *', 'SELECT cleanup_expired_auth_data();');

-- Add comments for documentation
COMMENT ON TABLE user_sessions IS 'Active user sessions for security tracking and analytics';
COMMENT ON TABLE refresh_tokens IS 'JWT refresh tokens for secure authentication';
COMMENT ON TABLE password_resets IS 'Password reset tokens for secure password recovery';
COMMENT ON TABLE email_verifications IS 'Email verification tokens for account verification';

COMMENT ON COLUMN user_sessions.session_token IS 'Unique session identifier';
COMMENT ON COLUMN user_sessions.ip_address IS 'IP address of the session for security tracking';
COMMENT ON COLUMN user_sessions.device_type IS 'Type of device used: mobile, tablet, desktop';
COMMENT ON COLUMN user_sessions.expires_at IS 'When the session expires';

COMMENT ON COLUMN refresh_tokens.token IS 'JWT refresh token for obtaining new access tokens';
COMMENT ON COLUMN refresh_tokens.is_revoked IS 'Whether the token has been revoked for security';
COMMENT ON COLUMN refresh_tokens.revoked_at IS 'When the token was revoked';

COMMENT ON COLUMN password_resets.token IS 'Secure token for password reset verification';
COMMENT ON COLUMN password_resets.is_used IS 'Whether the reset token has been used';
COMMENT ON COLUMN password_resets.used_at IS 'When the reset token was used';

COMMENT ON COLUMN email_verifications.token IS 'Secure token for email verification';
COMMENT ON COLUMN email_verifications.is_used IS 'Whether the verification token has been used';
COMMENT ON COLUMN email_verifications.used_at IS 'When the verification token was used';

-- Create view for active sessions summary
CREATE OR REPLACE VIEW active_sessions_summary AS
SELECT 
    u.id as user_id,
    u.email,
    u.full_name,
    COUNT(us.id) as active_sessions,
    MAX(us.last_activity) as last_activity,
    MAX(us.created_at) as latest_session_created
FROM users u
LEFT JOIN user_sessions us ON u.id = us.user_id AND us.is_active = TRUE AND us.expires_at > CURRENT_TIMESTAMP
GROUP BY u.id, u.email, u.full_name;

COMMENT ON VIEW active_sessions_summary IS 'Summary view of active user sessions for monitoring';

