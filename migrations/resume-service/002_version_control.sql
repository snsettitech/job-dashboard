-- Resume Service Migration 002: Version Control
-- Creates tables for resume versioning and history tracking

-- Create resume_versions table for version history
CREATE TABLE IF NOT EXISTS resume_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    
    -- Version content
    filename VARCHAR(255) NOT NULL,
    storage_key VARCHAR(500),
    storage_url VARCHAR(1000),
    file_size INTEGER NOT NULL,
    
    -- Content changes
    content_changes JSONB, -- Summary of changes from previous version
    optimization_notes TEXT,
    
    -- Version metadata
    created_by VARCHAR(100), -- user_id or system
    version_reason VARCHAR(255), -- optimization, manual_edit, etc.
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create resume_version_changes table for detailed change tracking
CREATE TABLE IF NOT EXISTS resume_version_changes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version_id UUID NOT NULL REFERENCES resume_versions(id) ON DELETE CASCADE,
    
    -- Change details
    change_type VARCHAR(50) NOT NULL, -- content_update, optimization, section_add, section_remove, etc.
    section_name VARCHAR(100), -- Which section was changed
    old_content TEXT, -- Previous content
    new_content TEXT, -- New content
    change_summary TEXT, -- Human-readable summary of the change
    
    -- Change metadata
    change_reason VARCHAR(255), -- Why the change was made
    ai_suggested BOOLEAN DEFAULT FALSE, -- Whether AI suggested this change
    user_approved BOOLEAN DEFAULT TRUE, -- Whether user approved the change
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_resume_versions_resume_id ON resume_versions(resume_id);
CREATE INDEX IF NOT EXISTS idx_resume_versions_version_number ON resume_versions(version_number);
CREATE INDEX IF NOT EXISTS idx_resume_versions_resume_number ON resume_versions(resume_id, version_number);
CREATE INDEX IF NOT EXISTS idx_resume_versions_created_at ON resume_versions(created_at);

CREATE INDEX IF NOT EXISTS idx_resume_version_changes_version_id ON resume_version_changes(version_id);
CREATE INDEX IF NOT EXISTS idx_resume_version_changes_change_type ON resume_version_changes(change_type);
CREATE INDEX IF NOT EXISTS idx_resume_version_changes_ai_suggested ON resume_version_changes(ai_suggested);
CREATE INDEX IF NOT EXISTS idx_resume_version_changes_created_at ON resume_version_changes(created_at);

-- Create function to get next version number
CREATE OR REPLACE FUNCTION get_next_version_number(p_resume_id UUID)
RETURNS INTEGER AS $$
DECLARE
    next_version INTEGER;
BEGIN
    SELECT COALESCE(MAX(version_number), 0) + 1
    INTO next_version
    FROM resume_versions
    WHERE resume_id = p_resume_id;
    
    RETURN next_version;
END;
$$ LANGUAGE plpgsql;

-- Create function to create new version
CREATE OR REPLACE FUNCTION create_resume_version(
    p_resume_id UUID,
    p_filename VARCHAR(255),
    p_storage_key VARCHAR(500),
    p_storage_url VARCHAR(1000),
    p_file_size INTEGER,
    p_content_changes JSONB,
    p_optimization_notes TEXT,
    p_created_by VARCHAR(100),
    p_version_reason VARCHAR(255)
)
RETURNS UUID AS $$
DECLARE
    new_version_id UUID;
    next_version_num INTEGER;
BEGIN
    -- Get next version number
    SELECT get_next_version_number(p_resume_id) INTO next_version_num;
    
    -- Create new version
    INSERT INTO resume_versions (
        resume_id,
        version_number,
        filename,
        storage_key,
        storage_url,
        file_size,
        content_changes,
        optimization_notes,
        created_by,
        version_reason
    ) VALUES (
        p_resume_id,
        next_version_num,
        p_filename,
        p_storage_key,
        p_storage_url,
        p_file_size,
        p_content_changes,
        p_optimization_notes,
        p_created_by,
        p_version_reason
    ) RETURNING id INTO new_version_id;
    
    -- Update resume version number
    UPDATE resumes 
    SET version_number = next_version_num,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_resume_id;
    
    RETURN new_version_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to get version history
CREATE OR REPLACE FUNCTION get_resume_version_history(p_resume_id UUID)
RETURNS TABLE (
    version_id UUID,
    version_number INTEGER,
    filename VARCHAR(255),
    file_size INTEGER,
    content_changes JSONB,
    optimization_notes TEXT,
    created_by VARCHAR(100),
    version_reason VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE,
    change_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        rv.id,
        rv.version_number,
        rv.filename,
        rv.file_size,
        rv.content_changes,
        rv.optimization_notes,
        rv.created_by,
        rv.version_reason,
        rv.created_at,
        COUNT(rvc.id)::INTEGER as change_count
    FROM resume_versions rv
    LEFT JOIN resume_version_changes rvc ON rv.id = rvc.version_id
    WHERE rv.resume_id = p_resume_id
    GROUP BY rv.id, rv.version_number, rv.filename, rv.file_size, 
             rv.content_changes, rv.optimization_notes, rv.created_by, 
             rv.version_reason, rv.created_at
    ORDER BY rv.version_number DESC;
END;
$$ LANGUAGE plpgsql;

-- Create function to compare versions
CREATE OR REPLACE FUNCTION compare_resume_versions(
    p_resume_id UUID,
    p_version1 INTEGER,
    p_version2 INTEGER
)
RETURNS TABLE (
    change_type VARCHAR(50),
    section_name VARCHAR(100),
    old_content TEXT,
    new_content TEXT,
    change_summary TEXT,
    change_reason VARCHAR(255),
    ai_suggested BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        rvc.change_type,
        rvc.section_name,
        rvc.old_content,
        rvc.new_content,
        rvc.change_summary,
        rvc.change_reason,
        rvc.ai_suggested
    FROM resume_version_changes rvc
    JOIN resume_versions rv ON rvc.version_id = rv.id
    WHERE rv.resume_id = p_resume_id 
    AND rv.version_number BETWEEN LEAST(p_version1, p_version2) AND GREATEST(p_version1, p_version2)
    ORDER BY rv.version_number, rvc.created_at;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically create initial version
CREATE OR REPLACE FUNCTION create_initial_version()
RETURNS TRIGGER AS $$
BEGIN
    -- Create initial version when resume is created
    INSERT INTO resume_versions (
        resume_id,
        version_number,
        filename,
        storage_key,
        storage_url,
        file_size,
        content_changes,
        created_by,
        version_reason
    ) VALUES (
        NEW.id,
        1,
        NEW.filename,
        NEW.storage_key,
        NEW.storage_url,
        NEW.file_size,
        '{"type": "initial_upload", "description": "Initial resume upload"}'::jsonb,
        'system',
        'initial_upload'
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for initial version creation
CREATE TRIGGER create_initial_resume_version
    AFTER INSERT ON resumes
    FOR EACH ROW
    EXECUTE FUNCTION create_initial_version();

-- Create view for resume version summary
CREATE OR REPLACE VIEW resume_version_summary AS
SELECT 
    r.id as resume_id,
    r.user_id,
    r.filename as current_filename,
    r.version_number as current_version,
    r.created_at as resume_created,
    r.updated_at as resume_updated,
    COUNT(rv.id) as total_versions,
    MAX(rv.created_at) as last_version_created,
    MAX(rv.version_number) as latest_version_number
FROM resumes r
LEFT JOIN resume_versions rv ON r.id = rv.resume_id
GROUP BY r.id, r.user_id, r.filename, r.version_number, r.created_at, r.updated_at;

-- Add comments for documentation
COMMENT ON TABLE resume_versions IS 'Version history for resumes with change tracking';
COMMENT ON TABLE resume_version_changes IS 'Detailed change tracking for resume versions';

COMMENT ON COLUMN resume_versions.version_number IS 'Sequential version number for the resume';
COMMENT ON COLUMN resume_versions.filename IS 'Filename for this specific version';
COMMENT ON COLUMN resume_versions.storage_key IS 'Storage provider key for this version';
COMMENT ON COLUMN resume_versions.content_changes IS 'JSON summary of changes from previous version';
COMMENT ON COLUMN resume_versions.optimization_notes IS 'Notes about optimizations made in this version';
COMMENT ON COLUMN resume_versions.created_by IS 'User ID or system identifier that created this version';
COMMENT ON COLUMN resume_versions.version_reason IS 'Reason for creating this version: optimization, manual_edit, etc.';

COMMENT ON COLUMN resume_version_changes.change_type IS 'Type of change: content_update, optimization, section_add, section_remove, etc.';
COMMENT ON COLUMN resume_version_changes.section_name IS 'Name of the resume section that was changed';
COMMENT ON COLUMN resume_version_changes.old_content IS 'Previous content before the change';
COMMENT ON COLUMN resume_version_changes.new_content IS 'New content after the change';
COMMENT ON COLUMN resume_version_changes.change_summary IS 'Human-readable summary of what changed';
COMMENT ON COLUMN resume_version_changes.change_reason IS 'Reason why this change was made';
COMMENT ON COLUMN resume_version_changes.ai_suggested IS 'Whether AI suggested this change';
COMMENT ON COLUMN resume_version_changes.user_approved IS 'Whether user approved this change';

COMMENT ON FUNCTION get_next_version_number(UUID) IS 'Returns the next version number for a resume';
COMMENT ON FUNCTION create_resume_version(UUID, VARCHAR, VARCHAR, VARCHAR, INTEGER, JSONB, TEXT, VARCHAR, VARCHAR) IS 'Creates a new resume version with all metadata';
COMMENT ON FUNCTION get_resume_version_history(UUID) IS 'Returns complete version history for a resume';
COMMENT ON FUNCTION compare_resume_versions(UUID, INTEGER, INTEGER) IS 'Compares two versions of a resume and returns differences';
COMMENT ON FUNCTION create_initial_version() IS 'Automatically creates initial version when resume is uploaded';
COMMENT ON VIEW resume_version_summary IS 'Summary view of resume versions for quick reference';

