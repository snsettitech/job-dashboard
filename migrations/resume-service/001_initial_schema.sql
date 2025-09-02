-- Resume Service Migration 001: Initial Schema
-- Creates the core resumes table and storage configuration

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create storage_configs table for cloud storage configuration
CREATE TABLE IF NOT EXISTS storage_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Storage provider configuration
    provider VARCHAR(50) NOT NULL, -- s3, railway, local
    bucket_name VARCHAR(255),
    region VARCHAR(50),
    endpoint_url VARCHAR(500), -- For Railway or custom S3-compatible storage
    
    -- Authentication
    access_key_id VARCHAR(255),
    secret_access_key VARCHAR(500), -- Encrypted
    session_token VARCHAR(1000), -- For temporary credentials
    
    -- Configuration
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    max_file_size INTEGER DEFAULT 10485760, -- 10MB default
    allowed_file_types JSONB, -- Allowed MIME types
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create resumes table for main resume records
CREATE TABLE IF NOT EXISTS resumes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL, -- References user service
    
    -- File information
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL, -- pdf, docx, txt, jpg, png
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    
    -- Cloud storage information
    storage_provider VARCHAR(50) DEFAULT 's3', -- s3, railway, local
    storage_bucket VARCHAR(255),
    storage_key VARCHAR(500), -- S3 key or Railway path
    storage_url VARCHAR(1000), -- Public URL if available
    storage_region VARCHAR(50),
    
    -- Content extraction
    extracted_text TEXT,
    cleaned_text TEXT,
    word_count INTEGER,
    character_count INTEGER,
    
    -- AI Analysis results
    extracted_skills JSONB, -- Array of skills found
    contact_info JSONB, -- Email, phone, linkedin, etc.
    experience_summary JSONB, -- Structured experience data
    education_summary JSONB, -- Education information
    achievements JSONB, -- Quantified achievements
    sections_identified JSONB, -- Resume sections found
    
    -- Quality assessment
    quality_score FLOAT,
    quality_feedback JSONB,
    completeness_score FLOAT,
    
    -- Version control
    version_number INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,
    
    -- Processing status
    processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    processing_error TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_storage_configs_provider_active ON storage_configs(provider, is_active);
CREATE INDEX IF NOT EXISTS idx_storage_configs_is_default ON storage_configs(is_default);

CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_resumes_user_active ON resumes(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_resumes_status ON resumes(processing_status);
CREATE INDEX IF NOT EXISTS idx_resumes_created ON resumes(created_at);
CREATE INDEX IF NOT EXISTS idx_resumes_file_type ON resumes(file_type);
CREATE INDEX IF NOT EXISTS idx_resumes_storage_provider ON resumes(storage_provider);

-- Create updated_at trigger function (if not exists from user service)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_storage_configs_updated_at 
    BEFORE UPDATE ON storage_configs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_resumes_updated_at 
    BEFORE UPDATE ON resumes 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to get default storage config
CREATE OR REPLACE FUNCTION get_default_storage_config()
RETURNS TABLE (
    id UUID,
    provider VARCHAR(50),
    bucket_name VARCHAR(255),
    region VARCHAR(50),
    endpoint_url VARCHAR(500),
    max_file_size INTEGER,
    allowed_file_types JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sc.id,
        sc.provider,
        sc.bucket_name,
        sc.region,
        sc.endpoint_url,
        sc.max_file_size,
        sc.allowed_file_types
    FROM storage_configs sc
    WHERE sc.is_default = TRUE AND sc.is_active = TRUE
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Create function to validate file upload
CREATE OR REPLACE FUNCTION validate_file_upload(
    p_file_size INTEGER,
    p_mime_type VARCHAR(100),
    p_user_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    config_record RECORD;
BEGIN
    -- Get default storage config
    SELECT * INTO config_record FROM get_default_storage_config();
    
    -- Check if config exists
    IF config_record.id IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Check file size
    IF p_file_size > config_record.max_file_size THEN
        RETURN FALSE;
    END IF;
    
    -- Check file type
    IF config_record.allowed_file_types IS NOT NULL AND 
       NOT (config_record.allowed_file_types ? p_mime_type) THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Insert default storage configurations
INSERT INTO storage_configs (
    provider, 
    bucket_name, 
    region, 
    is_default, 
    max_file_size, 
    allowed_file_types
) VALUES 
-- S3 Configuration
(
    's3',
    'resume-storage',
    'us-east-1',
    TRUE,
    10485760, -- 10MB
    '["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain", "image/jpeg", "image/png"]'::jsonb
),
-- Railway Configuration
(
    'railway',
    'resume-storage-railway',
    'us-east-1',
    FALSE,
    10485760, -- 10MB
    '["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain", "image/jpeg", "image/png"]'::jsonb
),
-- Local Configuration
(
    'local',
    'local-storage',
    NULL,
    FALSE,
    10485760, -- 10MB
    '["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain", "image/jpeg", "image/png"]'::jsonb
)
ON CONFLICT DO NOTHING;

-- Add comments for documentation
COMMENT ON TABLE storage_configs IS 'Cloud storage configuration for resume file storage';
COMMENT ON TABLE resumes IS 'Main resume records with metadata and extracted content';

COMMENT ON COLUMN storage_configs.provider IS 'Storage provider: s3, railway, local';
COMMENT ON COLUMN storage_configs.bucket_name IS 'Storage bucket or container name';
COMMENT ON COLUMN storage_configs.endpoint_url IS 'Custom endpoint URL for S3-compatible storage';
COMMENT ON COLUMN storage_configs.secret_access_key IS 'Encrypted secret access key';
COMMENT ON COLUMN storage_configs.max_file_size IS 'Maximum allowed file size in bytes';
COMMENT ON COLUMN storage_configs.allowed_file_types IS 'JSON array of allowed MIME types';

COMMENT ON COLUMN resumes.user_id IS 'Reference to user in user service';
COMMENT ON COLUMN resumes.filename IS 'Internal filename for storage';
COMMENT ON COLUMN resumes.original_filename IS 'Original filename uploaded by user';
COMMENT ON COLUMN resumes.file_type IS 'File extension: pdf, docx, txt, jpg, png';
COMMENT ON COLUMN resumes.storage_key IS 'Storage provider key/path for the file';
COMMENT ON COLUMN resumes.storage_url IS 'Public URL if available for direct access';
COMMENT ON COLUMN resumes.extracted_text IS 'Raw text extracted from the document';
COMMENT ON COLUMN resumes.cleaned_text IS 'Processed and cleaned text content';
COMMENT ON COLUMN resumes.extracted_skills IS 'JSON array of skills found in the resume';
COMMENT ON COLUMN resumes.contact_info IS 'JSON object with extracted contact information';
COMMENT ON COLUMN resumes.experience_summary IS 'JSON array of structured experience data';
COMMENT ON COLUMN resumes.education_summary IS 'JSON array of education information';
COMMENT ON COLUMN resumes.achievements IS 'JSON array of quantified achievements';
COMMENT ON COLUMN resumes.sections_identified IS 'JSON array of resume sections found';
COMMENT ON COLUMN resumes.quality_score IS 'Overall quality score 0-100';
COMMENT ON COLUMN resumes.quality_feedback IS 'JSON object with detailed quality feedback';
COMMENT ON COLUMN resumes.completeness_score IS 'Completeness score 0-100';
COMMENT ON COLUMN resumes.version_number IS 'Version number for version control';
COMMENT ON COLUMN resumes.is_active IS 'Whether this is the active version';
COMMENT ON COLUMN resumes.is_public IS 'Whether the resume is publicly accessible';
COMMENT ON COLUMN resumes.processing_status IS 'Processing status: pending, processing, completed, failed';
COMMENT ON COLUMN resumes.processing_error IS 'Error message if processing failed';

COMMENT ON FUNCTION get_default_storage_config() IS 'Returns the default active storage configuration';
COMMENT ON FUNCTION validate_file_upload(INTEGER, VARCHAR, UUID) IS 'Validates file upload against storage configuration';

