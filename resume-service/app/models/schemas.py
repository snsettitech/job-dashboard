# resume-service/app/models/schemas.py
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# Enums
class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    JPG = "jpg"
    PNG = "png"

class StorageProvider(str, Enum):
    S3 = "s3"
    RAILWAY = "railway"
    LOCAL = "local"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalysisType(str, Enum):
    SKILLS = "skills"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    OVERALL = "overall"

# Base Models
class BaseResponse(BaseModel):
    status: str = "success"
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Resume Upload Models
class ResumeUploadRequest(BaseModel):
    user_id: str = Field(..., description="User ID uploading the resume")
    filename: str = Field(..., min_length=1, max_length=255)
    file_type: FileType
    file_size: int = Field(..., gt=0, le=10*1024*1024)  # Max 10MB
    mime_type: str = Field(..., min_length=1, max_length=100)
    is_public: bool = Field(default=False)
    
    @validator('file_size')
    def validate_file_size(cls, v):
        if v > 10 * 1024 * 1024:  # 10MB
            raise ValueError('File size must be less than 10MB')
        return v

class ResumeUploadResponse(BaseModel):
    resume_id: str
    upload_url: str
    storage_key: str
    expires_at: datetime
    status: str = "pending"

# Resume Models
class ResumeBase(BaseModel):
    filename: str
    original_filename: str
    file_type: FileType
    file_size: int
    mime_type: str
    storage_provider: StorageProvider = StorageProvider.S3
    is_public: bool = False

class ResumeCreate(ResumeBase):
    user_id: str

class ResumeUpdate(BaseModel):
    filename: Optional[str] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None

class ResumeResponse(ResumeBase):
    id: str
    user_id: str
    storage_bucket: Optional[str] = None
    storage_key: Optional[str] = None
    storage_url: Optional[str] = None
    storage_region: Optional[str] = None
    extracted_text: Optional[str] = None
    cleaned_text: Optional[str] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    extracted_skills: Optional[List[str]] = None
    contact_info: Optional[Dict[str, Any]] = None
    experience_summary: Optional[Dict[str, Any]] = None
    education_summary: Optional[Dict[str, Any]] = None
    achievements: Optional[List[str]] = None
    sections_identified: Optional[List[str]] = None
    quality_score: Optional[float] = None
    quality_feedback: Optional[List[str]] = None
    completeness_score: Optional[float] = None
    version_number: int = 1
    is_active: bool = True
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    processing_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Resume Version Models
class ResumeVersionCreate(BaseModel):
    resume_id: str
    version_number: int
    filename: str
    storage_key: Optional[str] = None
    storage_url: Optional[str] = None
    file_size: int
    content_changes: Optional[Dict[str, Any]] = None
    optimization_notes: Optional[str] = None
    created_by: Optional[str] = None
    version_reason: Optional[str] = None

class ResumeVersionResponse(BaseModel):
    id: str
    resume_id: str
    version_number: int
    filename: str
    storage_key: Optional[str] = None
    storage_url: Optional[str] = None
    file_size: int
    content_changes: Optional[Dict[str, Any]] = None
    optimization_notes: Optional[str] = None
    created_by: Optional[str] = None
    version_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Resume Optimization Models
class ResumeOptimizationRequest(BaseModel):
    resume_id: str
    target_job_title: Optional[str] = Field(None, max_length=255)
    target_company: Optional[str] = Field(None, max_length=255)
    target_industry: Optional[str] = Field(None, max_length=100)
    job_description: Optional[str] = None
    optimization_model: Optional[str] = Field(None, max_length=100)

class ResumeOptimizationResponse(BaseModel):
    id: str
    resume_id: str
    target_job_title: Optional[str] = None
    target_company: Optional[str] = None
    target_industry: Optional[str] = None
    job_description: Optional[str] = None
    optimized_content: Optional[str] = None
    improvements_made: Optional[List[str]] = None
    keywords_added: Optional[List[str]] = None
    keywords_removed: Optional[List[str]] = None
    ats_score_before: Optional[float] = None
    ats_score_after: Optional[float] = None
    match_score: Optional[float] = None
    confidence_score: Optional[float] = None
    optimization_model: Optional[str] = None
    processing_time: Optional[float] = None
    tokens_used: Optional[int] = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Resume Analysis Models
class ResumeAnalysisRequest(BaseModel):
    resume_id: str
    analysis_type: AnalysisType
    analysis_model: Optional[str] = Field(None, max_length=100)

class ResumeAnalysisResponse(BaseModel):
    id: str
    resume_id: str
    analysis_type: AnalysisType
    analysis_data: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    score: Optional[float] = None
    max_score: Optional[float] = None
    percentile: Optional[float] = None
    analysis_model: Optional[str] = None
    processing_time: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Storage Configuration Models
class StorageConfigCreate(BaseModel):
    provider: StorageProvider
    bucket_name: Optional[str] = Field(None, max_length=255)
    region: Optional[str] = Field(None, max_length=50)
    endpoint_url: Optional[str] = Field(None, max_length=500)
    access_key_id: Optional[str] = Field(None, max_length=255)
    secret_access_key: Optional[str] = Field(None, max_length=500)
    session_token: Optional[str] = Field(None, max_length=1000)
    is_default: bool = False
    max_file_size: int = Field(default=10*1024*1024, gt=0)  # 10MB default
    allowed_file_types: Optional[List[str]] = None

class StorageConfigResponse(BaseModel):
    id: str
    provider: StorageProvider
    bucket_name: Optional[str] = None
    region: Optional[str] = None
    endpoint_url: Optional[str] = None
    is_active: bool = True
    is_default: bool = False
    max_file_size: int
    allowed_file_types: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# File Processing Models
class FileProcessingResult(BaseModel):
    raw_text: str
    cleaned_text: str
    structured_info: Dict[str, Any]
    metadata: Dict[str, Any]

class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None

class SkillsInfo(BaseModel):
    raw_skills_text: str
    identified_skills: List[str]
    skill_count: int

class ExperienceInfo(BaseModel):
    has_experience_section: bool
    years_pattern_found: bool
    company_patterns: int

class EducationInfo(BaseModel):
    has_education_section: bool
    degrees_mentioned: List[str]
    graduation_years: List[str]

class StructuredInfo(BaseModel):
    contact_info: ContactInfo
    skills: SkillsInfo
    experience: ExperienceInfo
    education: EducationInfo
    sections: List[str]

# Quality Assessment Models
class QualityAssessment(BaseModel):
    quality_score: float
    max_score: float = 100
    feedback: List[str]
    grade: str  # Excellent, Good, Fair, Needs Improvement

# List Response Models
class ResumeListResponse(BaseModel):
    resumes: List[ResumeResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class ResumeVersionListResponse(BaseModel):
    versions: List[ResumeVersionResponse]
    total_count: int
    resume_id: str

class ResumeOptimizationListResponse(BaseModel):
    optimizations: List[ResumeOptimizationResponse]
    total_count: int
    resume_id: str

class ResumeAnalysisListResponse(BaseModel):
    analyses: List[ResumeAnalysisResponse]
    total_count: int
    resume_id: str

# Health and Status Models
class ServiceHealth(BaseModel):
    status: str
    timestamp: datetime
    version: str
    uptime: float
    database_status: str
    storage_status: str

class ProcessingStatusResponse(BaseModel):
    resume_id: str
    status: ProcessingStatus
    progress: Optional[float] = None  # 0-100
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None

