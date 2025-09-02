# ai-service/app/models/ai_models.py - AI Service Database Models
from sqlalchemy import Column, String, Text, Float, DateTime, Boolean, Integer, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class AIProcessingSession(Base):
    """AI processing session tracking"""
    __tablename__ = "ai_processing_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Optional user tracking
    operation_type = Column(String(50), nullable=False)  # job_match, resume_optimization, etc.
    status = Column(String(20), nullable=False, default="processing")  # processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    # AI processing metadata
    ai_calls_made = Column(Integer, default=0)
    successful_ai_calls = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    model_used = Column(String(100), nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    fallback_used = Column(Boolean, default=False)
    
    # Relationships
    embeddings = relationship("Embedding", back_populates="session")
    optimizations = relationship("ResumeOptimization", back_populates="session")
    analyses = relationship("JobMatchAnalysis", back_populates="session")
    
    __table_args__ = (
        Index('idx_session_user_created', 'user_id', 'created_at'),
        Index('idx_session_status', 'status'),
    )

class Embedding(Base):
    """Vector embeddings storage"""
    __tablename__ = "embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('ai_processing_sessions.id'), nullable=False)
    text_hash = Column(String(64), nullable=False, index=True)  # Hash of original text
    text_type = Column(String(50), nullable=False)  # resume, job_description, skills, etc.
    embedding_vector = Column(ARRAY(Float), nullable=False)  # PostgreSQL array of floats
    model_name = Column(String(100), nullable=False)  # text-embedding-3-small, etc.
    dimensions = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Metadata
    text_preview = Column(String(500), nullable=True)  # First 500 chars for reference
    token_count = Column(Integer, nullable=True)
    
    # Relationships
    session = relationship("AIProcessingSession", back_populates="embeddings")
    
    __table_args__ = (
        Index('idx_embedding_text_hash', 'text_hash'),
        Index('idx_embedding_type', 'text_type'),
        Index('idx_embedding_model', 'model_name'),
    )

class ResumeOptimization(Base):
    """Resume optimization results"""
    __tablename__ = "resume_optimizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('ai_processing_sessions.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Original content
    original_resume_hash = Column(String(64), nullable=False, index=True)
    original_resume_preview = Column(String(1000), nullable=True)
    job_description_hash = Column(String(64), nullable=False, index=True)
    job_description_preview = Column(String(1000), nullable=True)
    
    # Optimization results
    optimized_resume = Column(Text, nullable=False)
    improvements_made = Column(JSON, nullable=True)  # Array of improvement descriptions
    keywords_added = Column(JSON, nullable=True)  # Array of keywords
    ats_score_improvement = Column(String(20), nullable=True)  # e.g., "+35%"
    match_score_prediction = Column(Float, nullable=True)
    
    # Quality metrics
    confidence_score = Column(Float, nullable=True)
    confidence_level = Column(String(20), nullable=True)  # Very High, High, Medium, Low
    quality_validation_passed = Column(Boolean, default=False)
    
    # Processing metadata
    model_used = Column(String(100), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    session = relationship("AIProcessingSession", back_populates="optimizations")
    
    __table_args__ = (
        Index('idx_optimization_user_created', 'user_id', 'created_at'),
        Index('idx_optimization_confidence', 'confidence_score'),
        Index('idx_optimization_quality', 'quality_validation_passed'),
    )

class JobMatchAnalysis(Base):
    """Job matching analysis results"""
    __tablename__ = "job_match_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('ai_processing_sessions.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Input content
    resume_hash = Column(String(64), nullable=False, index=True)
    resume_preview = Column(String(1000), nullable=True)
    job_description_hash = Column(String(64), nullable=False, index=True)
    job_description_preview = Column(String(1000), nullable=True)
    
    # Analysis results
    match_scores = Column(JSON, nullable=False)  # Overall, skills, experience, etc.
    recommendation = Column(Text, nullable=True)
    detailed_analysis = Column(JSON, nullable=True)  # Detailed breakdown
    
    # Semantic analysis
    semantic_similarity = Column(Float, nullable=True)
    skills_overlap = Column(JSON, nullable=True)  # Matching and missing skills
    experience_alignment = Column(Text, nullable=True)
    
    # Quality metrics
    confidence_score = Column(Float, nullable=True)
    confidence_level = Column(String(20), nullable=True)
    analysis_depth = Column(String(20), nullable=True)  # high, medium, low
    
    # Processing metadata
    model_used = Column(String(100), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    session = relationship("AIProcessingSession", back_populates="analyses")
    
    __table_args__ = (
        Index('idx_analysis_user_created', 'user_id', 'created_at'),
        Index('idx_analysis_confidence', 'confidence_score'),
        Index('idx_analysis_similarity', 'semantic_similarity'),
    )

class VectorIndex(Base):
    """Vector index for similarity search"""
    __tablename__ = "vector_indices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    index_name = Column(String(100), unique=True, nullable=False, index=True)
    index_type = Column(String(50), nullable=False)  # faiss, chroma, etc.
    dimensions = Column(Integer, nullable=False)
    total_vectors = Column(Integer, default=0)
    
    # Index metadata
    model_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Configuration
    index_config = Column(JSON, nullable=True)  # Index-specific configuration
    is_active = Column(Boolean, default=True)
    
    __table_args__ = (
        Index('idx_vector_index_type', 'index_type'),
        Index('idx_vector_index_active', 'is_active'),
    )

class AIUsageMetrics(Base):
    """AI service usage metrics and analytics"""
    __tablename__ = "ai_usage_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(DateTime, nullable=False, index=True)
    operation_type = Column(String(50), nullable=False, index=True)
    
    # Usage counts
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    
    # Performance metrics
    avg_processing_time_ms = Column(Float, nullable=True)
    total_tokens_used = Column(Integer, default=0)
    avg_tokens_per_request = Column(Float, nullable=True)
    
    # Quality metrics
    avg_confidence_score = Column(Float, nullable=True)
    high_confidence_requests = Column(Integer, default=0)  # confidence >= 80
    
    # Error tracking
    error_types = Column(JSON, nullable=True)  # Count of different error types
    
    # Model usage
    model_usage = Column(JSON, nullable=True)  # Usage by model type
    
    __table_args__ = (
        Index('idx_metrics_date_type', 'date', 'operation_type'),
        Index('idx_metrics_operation', 'operation_type'),
    )

class AIServiceConfig(Base):
    """AI service configuration and settings"""
    __tablename__ = "ai_service_config"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=False)
    config_type = Column(String(50), nullable=False)  # string, int, float, bool, json
    
    # Metadata
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_config_active', 'is_active'),
        Index('idx_config_type', 'config_type'),
    )



