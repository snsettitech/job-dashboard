# resume-service/app/models/resume_models.py
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, Float, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Resume(Base):
    """Resume documents with cloud storage integration"""
    __tablename__ = "resumes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx, txt, jpg, png
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # Cloud storage information
    storage_provider = Column(String(50), default="s3")  # s3, railway, local
    storage_bucket = Column(String(255))
    storage_key = Column(String(500))  # S3 key or Railway path
    storage_url = Column(String(1000))  # Public URL if available
    storage_region = Column(String(50))
    
    # Content extraction
    extracted_text = Column(Text)
    cleaned_text = Column(Text)
    word_count = Column(Integer)
    character_count = Column(Integer)
    
    # AI Analysis results
    extracted_skills = Column(JSON)  # Array of skills found
    contact_info = Column(JSON)  # Email, phone, linkedin, etc.
    experience_summary = Column(JSON)  # Structured experience data
    education_summary = Column(JSON)  # Education information
    achievements = Column(JSON)  # Quantified achievements
    sections_identified = Column(JSON)  # Resume sections found
    
    # Quality assessment
    quality_score = Column(Float)
    quality_feedback = Column(JSON)
    completeness_score = Column(Float)
    
    # Version control
    version_number = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    
    # Processing status
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processing_error = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    versions = relationship("ResumeVersion", back_populates="resume", cascade="all, delete-orphan")
    optimizations = relationship("ResumeOptimization", back_populates="resume", cascade="all, delete-orphan")
    analyses = relationship("ResumeAnalysis", back_populates="resume", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_resume_user_active', 'user_id', 'is_active'),
        Index('idx_resume_status', 'processing_status'),
        Index('idx_resume_created', 'created_at'),
    )

class ResumeVersion(Base):
    """Version history for resumes"""
    __tablename__ = "resume_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey('resumes.id'), nullable=False)
    version_number = Column(Integer, nullable=False)
    
    # Version content
    filename = Column(String(255), nullable=False)
    storage_key = Column(String(500))
    storage_url = Column(String(1000))
    file_size = Column(Integer, nullable=False)
    
    # Content changes
    content_changes = Column(JSON)  # Summary of changes from previous version
    optimization_notes = Column(Text)
    
    # Version metadata
    created_by = Column(String(100))  # user_id or system
    version_reason = Column(String(255))  # optimization, manual_edit, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resume = relationship("Resume", back_populates="versions")
    
    # Indexes
    __table_args__ = (
        Index('idx_version_resume_number', 'resume_id', 'version_number'),
    )

class ResumeOptimization(Base):
    """Resume optimization attempts and results"""
    __tablename__ = "resume_optimizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey('resumes.id'), nullable=False)
    
    # Optimization target
    target_job_title = Column(String(255))
    target_company = Column(String(255))
    target_industry = Column(String(100))
    job_description = Column(Text)
    
    # Optimization results
    optimized_content = Column(Text)
    improvements_made = Column(JSON)  # List of specific improvements
    keywords_added = Column(JSON)  # Keywords added for ATS
    keywords_removed = Column(JSON)  # Keywords removed
    
    # Scoring
    ats_score_before = Column(Float)
    ats_score_after = Column(Float)
    match_score = Column(Float)
    confidence_score = Column(Float)
    
    # Processing metadata
    optimization_model = Column(String(100))  # AI model used
    processing_time = Column(Float)  # Seconds taken
    tokens_used = Column(Integer)
    
    # Status
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    resume = relationship("Resume", back_populates="optimizations")
    
    # Indexes
    __table_args__ = (
        Index('idx_optimization_resume_status', 'resume_id', 'status'),
        Index('idx_optimization_created', 'created_at'),
    )

class ResumeAnalysis(Base):
    """Detailed resume analysis results"""
    __tablename__ = "resume_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey('resumes.id'), nullable=False)
    
    # Analysis type
    analysis_type = Column(String(50), nullable=False)  # skills, experience, education, overall
    
    # Analysis results
    analysis_data = Column(JSON)  # Detailed analysis results
    recommendations = Column(JSON)  # Improvement recommendations
    strengths = Column(JSON)  # Identified strengths
    weaknesses = Column(JSON)  # Areas for improvement
    
    # Scoring
    score = Column(Float)
    max_score = Column(Float)
    percentile = Column(Float)
    
    # Processing metadata
    analysis_model = Column(String(100))
    processing_time = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    resume = relationship("Resume", back_populates="analyses")
    
    # Indexes
    __table_args__ = (
        Index('idx_analysis_resume_type', 'resume_id', 'analysis_type'),
    )

class StorageConfig(Base):
    """Cloud storage configuration"""
    __tablename__ = "storage_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Storage provider configuration
    provider = Column(String(50), nullable=False)  # s3, railway, local
    bucket_name = Column(String(255))
    region = Column(String(50))
    endpoint_url = Column(String(500))  # For Railway or custom S3-compatible storage
    
    # Authentication
    access_key_id = Column(String(255))
    secret_access_key = Column(String(500))  # Encrypted
    session_token = Column(String(1000))  # For temporary credentials
    
    # Configuration
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    max_file_size = Column(Integer, default=10 * 1024 * 1024)  # 10MB default
    allowed_file_types = Column(JSON)  # Allowed MIME types
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_storage_provider_active', 'provider', 'is_active'),
    )

