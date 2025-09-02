# ai-service/app/models/schemas.py - AI Service Pydantic Schemas
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime
import uuid

# Enums
class OperationType(str, Enum):
    JOB_MATCH = "job_match"
    RESUME_OPTIMIZATION = "resume_optimization"
    ENHANCED_OPTIMIZATION = "enhanced_optimization"
    BATCH_ANALYSIS = "batch_analysis"
    EMBEDDING_GENERATION = "embedding_generation"

class ProcessingStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ConfidenceLevel(str, Enum):
    VERY_HIGH = "Very High"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class AnalysisDepth(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class EmbeddingModel(str, Enum):
    TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"
    TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"
    TEXT_EMBEDDING_ADA_002 = "text-embedding-ada-002"

class ChatModel(str, Enum):
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_3_5_TURBO = "gpt-3.5-turbo"

# Base Models
class BaseRequest(BaseModel):
    user_id: Optional[uuid.UUID] = Field(None, description="Optional user ID for tracking")
    
    class Config:
        json_encoders = {
            uuid.UUID: str
        }

class BaseResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Job Match Analysis Schemas
class JobMatchRequest(BaseRequest):
    resume_text: str = Field(..., min_length=50, max_length=50000, description="Resume text content")
    job_description: str = Field(..., min_length=50, max_length=50000, description="Job description text")
    include_detailed_analysis: bool = Field(True, description="Include detailed analysis breakdown")
    use_enhanced_analysis: bool = Field(False, description="Use enhanced analysis with multiple AI calls")
    
    @validator('resume_text', 'job_description')
    def validate_text_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Text content cannot be empty")
        if len(v.strip()) < 50:
            raise ValueError("Text content must be at least 50 characters")
        return v.strip()

class MatchScores(BaseModel):
    overall: float = Field(..., ge=0.0, le=1.0, description="Overall match score")
    skills: float = Field(..., ge=0.0, le=1.0, description="Skills match score")
    experience: float = Field(..., ge=0.0, le=1.0, description="Experience match score")
    location: float = Field(..., ge=0.0, le=1.0, description="Location compatibility score")
    salary: float = Field(..., ge=0.0, le=1.0, description="Salary expectation alignment score")

class DetailedAnalysis(BaseModel):
    matching_skills: List[str] = Field(default_factory=list, description="Skills that match the job")
    missing_skills: List[str] = Field(default_factory=list, description="Skills missing from resume")
    experience_alignment: str = Field(..., description="Analysis of experience alignment")
    location_analysis: str = Field(..., description="Location compatibility analysis")
    salary_analysis: str = Field(..., description="Salary expectation analysis")
    competitive_advantages: List[str] = Field(default_factory=list, description="Unique advantages")
    areas_for_improvement: List[str] = Field(default_factory=list, description="Areas to improve")

class JobMatchResponse(BaseResponse):
    session_id: str = Field(..., description="Processing session ID")
    match_scores: MatchScores = Field(..., description="Detailed match scores")
    recommendation: str = Field(..., description="AI-generated recommendation")
    confidence_score: float = Field(..., ge=0.0, le=100.0, description="Confidence in analysis")
    confidence_level: ConfidenceLevel = Field(..., description="Confidence level category")
    confidence_interval: str = Field(..., description="Confidence interval")
    detailed_analysis: Optional[DetailedAnalysis] = Field(None, description="Detailed analysis breakdown")
    semantic_similarity: float = Field(..., ge=0.0, le=1.0, description="Semantic similarity score")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")

# Resume Optimization Schemas
class ResumeOptimizationRequest(BaseRequest):
    resume_text: str = Field(..., min_length=50, max_length=50000, description="Original resume text")
    job_description: str = Field(..., min_length=50, max_length=50000, description="Target job description")
    optimization_level: str = Field("standard", regex="^(standard|enhanced|premium)$", description="Optimization level")
    include_analysis: bool = Field(True, description="Include gap analysis with optimization")
    preserve_formatting: bool = Field(True, description="Preserve original formatting structure")
    
    @validator('resume_text', 'job_description')
    def validate_text_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Text content cannot be empty")
        if len(v.strip()) < 50:
            raise ValueError("Text content must be at least 50 characters")
        return v.strip()

class OptimizationImprovement(BaseModel):
    category: str = Field(..., description="Improvement category")
    description: str = Field(..., description="Description of improvement")
    impact: str = Field(..., description="Expected impact of improvement")
    before_example: Optional[str] = Field(None, description="Before example")
    after_example: Optional[str] = Field(None, description="After example")

class ResumeOptimizationResponse(BaseResponse):
    session_id: str = Field(..., description="Processing session ID")
    optimized_resume: str = Field(..., description="Optimized resume text")
    improvements_made: List[OptimizationImprovement] = Field(..., description="List of improvements made")
    keywords_added: List[str] = Field(..., description="Keywords added from job description")
    ats_score_improvement: str = Field(..., description="Estimated ATS score improvement")
    match_score_prediction: float = Field(..., ge=0.0, le=1.0, description="Predicted match score")
    optimization_summary: str = Field(..., description="Summary of optimization changes")
    confidence_score: float = Field(..., ge=0.0, le=100.0, description="Confidence in optimization")
    confidence_level: ConfidenceLevel = Field(..., description="Confidence level category")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    before_after_comparison: Dict[str, Any] = Field(default_factory=dict, description="Before/after comparison")

# Enhanced Optimization Schemas
class EnhancedOptimizationRequest(BaseRequest):
    resume_text: str = Field(..., min_length=50, max_length=50000, description="Original resume text")
    job_description: str = Field(..., min_length=50, max_length=50000, description="Target job description")
    user_context: Optional[Dict[str, Any]] = Field(None, description="Additional user context")
    optimization_focus: List[str] = Field(default_factory=list, description="Specific areas to focus on")
    
    @validator('resume_text', 'job_description')
    def validate_text_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Text content cannot be empty")
        if len(v.strip()) < 50:
            raise ValueError("Text content must be at least 50 characters")
        return v.strip()

class GapAnalysis(BaseModel):
    skills_gaps: List[str] = Field(default_factory=list, description="Missing skills identified")
    skills_to_emphasize: List[str] = Field(default_factory=list, description="Skills to emphasize")
    experience_repositioning: List[Dict[str, str]] = Field(default_factory=list, description="Experience reframing suggestions")
    weak_language_fixes: List[Dict[str, str]] = Field(default_factory=list, description="Language improvements")
    missing_keywords: List[str] = Field(default_factory=list, description="Missing keywords from job description")
    quantification_opportunities: List[str] = Field(default_factory=list, description="Opportunities to add metrics")
    competitive_advantages: List[str] = Field(default_factory=list, description="Unique competitive advantages")
    narrative_theme: str = Field(..., description="Recommended career narrative theme")
    priority_improvements: List[str] = Field(default_factory=list, description="Priority improvements to make")

class QualityValidation(BaseModel):
    executive_presence_score: float = Field(..., ge=0.0, le=10.0, description="Executive presence score")
    ats_optimization_score: float = Field(..., ge=0.0, le=10.0, description="ATS optimization score")
    quantified_impact_score: float = Field(..., ge=0.0, le=10.0, description="Quantified impact score")
    differentiation_score: float = Field(..., ge=0.0, le=10.0, description="Competitive differentiation score")
    readability_score: float = Field(..., ge=0.0, le=10.0, description="Readability score")
    overall_score: float = Field(..., ge=0.0, le=10.0, description="Overall quality score")
    needs_improvement: bool = Field(..., description="Whether further improvement is needed")
    specific_feedback: List[str] = Field(default_factory=list, description="Specific feedback for improvement")
    strengths: List[str] = Field(default_factory=list, description="Strengths identified")
    callback_improvement: str = Field(..., description="Estimated callback improvement")
    final_grade: str = Field(..., description="Final quality grade")

class EnhancedOptimizationResponse(BaseResponse):
    session_id: str = Field(..., description="Processing session ID")
    optimized_resume: str = Field(..., description="Enhanced optimized resume")
    analysis: GapAnalysis = Field(..., description="Comprehensive gap analysis")
    optimization_details: Dict[str, Any] = Field(..., description="Detailed optimization information")
    quality_scores: QualityValidation = Field(..., description="Quality validation scores")
    processing_stages: List[str] = Field(..., description="Processing stages completed")
    confidence_score: float = Field(..., ge=0.0, le=100.0, description="Confidence score")
    estimated_improvement: str = Field(..., description="Estimated improvement percentage")
    processing_date: datetime = Field(..., description="Processing completion date")

# Batch Analysis Schemas
class BatchJobAnalysisRequest(BaseRequest):
    resume_text: str = Field(..., min_length=50, max_length=50000, description="Resume text content")
    job_descriptions: List[str] = Field(..., min_items=1, max_items=10, description="List of job descriptions")
    include_rankings: bool = Field(True, description="Include job rankings")
    parallel_processing: bool = Field(True, description="Process jobs in parallel")
    
    @validator('resume_text')
    def validate_resume_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Resume text cannot be empty")
        if len(v.strip()) < 50:
            raise ValueError("Resume text must be at least 50 characters")
        return v.strip()
    
    @validator('job_descriptions')
    def validate_job_descriptions(cls, v):
        for i, job_desc in enumerate(v):
            if not job_desc or not job_desc.strip():
                raise ValueError(f"Job description {i+1} cannot be empty")
            if len(job_desc.strip()) < 50:
                raise ValueError(f"Job description {i+1} must be at least 50 characters")
        return [job.strip() for job in v]

class JobMatchResult(BaseModel):
    job_index: int = Field(..., description="Index of the job in the input list")
    job_preview: str = Field(..., description="Preview of the job description")
    match_scores: MatchScores = Field(..., description="Match scores for this job")
    recommendation: str = Field(..., description="Recommendation for this job")
    rank: int = Field(..., description="Rank among all jobs (1 = best match)")
    confidence_score: float = Field(..., ge=0.0, le=100.0, description="Confidence in analysis")

class BatchAnalysisResponse(BaseResponse):
    session_id: str = Field(..., description="Processing session ID")
    total_jobs_analyzed: int = Field(..., description="Total number of jobs analyzed")
    matches: List[JobMatchResult] = Field(..., description="Ranked list of job matches")
    best_match: Optional[JobMatchResult] = Field(None, description="Best matching job")
    summary: Dict[str, Any] = Field(..., description="Analysis summary statistics")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")

# Embedding Schemas
class EmbeddingRequest(BaseRequest):
    texts: List[str] = Field(..., min_items=1, max_items=100, description="Texts to embed")
    model: EmbeddingModel = Field(EmbeddingModel.TEXT_EMBEDDING_3_SMALL, description="Embedding model to use")
    store_embeddings: bool = Field(True, description="Store embeddings in database")
    
    @validator('texts')
    def validate_texts(cls, v):
        for i, text in enumerate(v):
            if not text or not text.strip():
                raise ValueError(f"Text {i+1} cannot be empty")
            if len(text.strip()) < 3:
                raise ValueError(f"Text {i+1} must be at least 3 characters")
        return [text.strip() for text in v]

class EmbeddingResponse(BaseResponse):
    session_id: str = Field(..., description="Processing session ID")
    embeddings: List[List[float]] = Field(..., description="Generated embeddings")
    model_used: str = Field(..., description="Model used for embedding generation")
    dimensions: int = Field(..., description="Embedding dimensions")
    token_counts: List[int] = Field(default_factory=list, description="Token counts for each text")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")

# Session Management Schemas
class SessionStatusResponse(BaseResponse):
    session_id: str = Field(..., description="Session ID")
    status: ProcessingStatus = Field(..., description="Current processing status")
    operation_type: OperationType = Field(..., description="Type of operation")
    progress_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Progress percentage")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    current_stage: Optional[str] = Field(None, description="Current processing stage")
    error_message: Optional[str] = Field(None, description="Error message if failed")

class SessionListResponse(BaseResponse):
    sessions: List[Dict[str, Any]] = Field(..., description="List of user sessions")
    total_sessions: int = Field(..., description="Total number of sessions")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")

# Health and Metrics Schemas
class HealthCheckResponse(BaseResponse):
    status: str = Field(..., description="Service health status")
    ai_service: str = Field(..., description="AI service status")
    embedding_model: str = Field(..., description="Embedding model status")
    chat_model: str = Field(..., description="Chat model status")
    database: str = Field(..., description="Database connection status")
    redis: str = Field(..., description="Redis connection status")
    vector_store: str = Field(..., description="Vector store status")
    last_check: datetime = Field(..., description="Last health check time")

class UsageMetricsResponse(BaseResponse):
    daily_optimizations: int = Field(..., description="Daily optimization count")
    success_rate: str = Field(..., description="Success rate percentage")
    avg_processing_time: str = Field(..., description="Average processing time")
    popular_job_types: List[str] = Field(..., description="Popular job types")
    avg_improvement: str = Field(..., description="Average improvement percentage")
    user_satisfaction: str = Field(..., description="User satisfaction score")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Token usage by model")
    error_rates: Dict[str, float] = Field(default_factory=dict, description="Error rates by operation")

# Error Response Schema
class ErrorResponse(BaseResponse):
    error_code: str = Field(..., description="Error code")
    error_type: str = Field(..., description="Type of error")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    retry_after: Optional[int] = Field(None, description="Retry after seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "AI processing failed",
                "error_code": "AI_PROCESSING_ERROR",
                "error_type": "AI_SERVICE_UNAVAILABLE",
                "details": {"original_error": "OpenAI API rate limit exceeded"},
                "retry_after": 60
            }
        }

class IndexType(str, Enum):
    """Pinecone index types"""
    RESUMES = "resumes"
    JOBS = "jobs"
    SKILLS = "skills"
    COMPANIES = "companies"

class VectorSearchRequest(BaseModel):
    """Request for vector similarity search"""
    query_text: str = Field(..., min_length=10, description="Text to search for")
    index_type: IndexType = Field(..., description="Type of index to search")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity threshold")
    filter_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata filters")
    
    @validator('query_text')
    def validate_query_text(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Query text must be at least 10 characters long')
        return v.strip()

class VectorUpsertRequest(BaseModel):
    """Request for upserting vectors to Pinecone"""
    content_id: str = Field(..., description="Unique identifier for the content")
    content_text: str = Field(..., min_length=10, description="Text content to embed")
    content_type: str = Field(..., description="Type of content (resume, job, skill, company)")
    user_id: Optional[str] = Field(default=None, description="User ID if applicable")
    session_id: Optional[str] = Field(default=None, description="Processing session ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    @validator('content_text')
    def validate_content_text(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Content text must be at least 10 characters long')
        return v.strip()

class VectorBatchUpsertRequest(BaseModel):
    """Request for batch upserting vectors"""
    vectors: List[VectorUpsertRequest] = Field(..., min_items=1, max_items=100, description="List of vectors to upsert")
    
    @validator('vectors')
    def validate_vectors(cls, v):
        if len(v) > 100:
            raise ValueError('Cannot upsert more than 100 vectors at once')
        return v

class SearchResult(BaseModel):
    """Result from vector similarity search"""
    content_id: str = Field(..., description="Content identifier")
    content_type: str = Field(..., description="Type of content")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Content metadata")
    content_preview: Optional[str] = Field(default=None, description="Preview of content")
    
    class Config:
        schema_extra = {
            "example": {
                "content_id": "resume_123",
                "content_type": "resume",
                "similarity_score": 0.85,
                "metadata": {
                    "user_id": "user_456",
                    "text_length": 1500,
                    "timestamp": "2024-01-15T10:30:00Z"
                },
                "content_preview": "Senior Software Engineer with 5+ years..."
            }
        }

class VectorSearchResponse(BaseModel):
    """Response from vector similarity search"""
    query_text: str = Field(..., description="Original query text")
    index_type: IndexType = Field(..., description="Index type searched")
    results: List[SearchResult] = Field(default_factory=list, description="Search results")
    total_results: int = Field(..., description="Total number of results found")
    search_time_ms: float = Field(..., description="Search execution time in milliseconds")
    
    class Config:
        schema_extra = {
            "example": {
                "query_text": "Python developer with React experience",
                "index_type": "jobs",
                "results": [
                    {
                        "content_id": "job_789",
                        "content_type": "job",
                        "similarity_score": 0.92,
                        "metadata": {"company": "TechCorp", "location": "San Francisco"},
                        "content_preview": "Senior Python Developer position..."
                    }
                ],
                "total_results": 1,
                "search_time_ms": 245.67
            }
        }

class JobMatchRequest(BaseModel):
    """Request for job-resume matching"""
    resume_text: str = Field(..., min_length=50, description="Resume content")
    job_ids: Optional[List[str]] = Field(default=None, description="Specific job IDs to match against")
    top_k: int = Field(default=20, ge=1, le=50, description="Number of matches to return")
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity threshold")
    user_id: Optional[str] = Field(default=None, description="User ID for personalization")
    
    @validator('resume_text')
    def validate_resume_text(cls, v):
        if len(v.strip()) < 50:
            raise ValueError('Resume text must be at least 50 characters long')
        return v.strip()

class JobMatchResult(BaseModel):
    """Result from job-resume matching"""
    job_id: str = Field(..., description="Job identifier")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    match_quality: str = Field(..., description="Match quality assessment")
    recommendation: str = Field(..., description="Recommendation text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Job metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "job_123",
                "similarity_score": 0.88,
                "match_quality": "Very Good",
                "recommendation": "Recommend - Very good match",
                "metadata": {
                    "title": "Senior Python Developer",
                    "company": "TechCorp",
                    "location": "San Francisco"
                }
            }
        }

class JobMatchResponse(BaseModel):
    """Response from job-resume matching"""
    resume_length: int = Field(..., description="Length of resume text")
    total_matches: int = Field(..., description="Total number of matches found")
    matches: List[JobMatchResult] = Field(default_factory=list, description="Job matches")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    
    class Config:
        schema_extra = {
            "example": {
                "resume_length": 1500,
                "total_matches": 5,
                "matches": [
                    {
                        "job_id": "job_123",
                        "similarity_score": 0.88,
                        "match_quality": "Very Good",
                        "recommendation": "Recommend - Very good match",
                        "metadata": {"title": "Senior Python Developer"}
                    }
                ],
                "processing_time_ms": 1234.56
            }
        }

class ResumeMatchRequest(BaseModel):
    """Request for resume-job matching (reverse matching)"""
    job_description: str = Field(..., min_length=50, description="Job description content")
    resume_ids: Optional[List[str]] = Field(default=None, description="Specific resume IDs to match against")
    top_k: int = Field(default=20, ge=1, le=50, description="Number of matches to return")
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity threshold")
    
    @validator('job_description')
    def validate_job_description(cls, v):
        if len(v.strip()) < 50:
            raise ValueError('Job description must be at least 50 characters long')
        return v.strip()

class ResumeMatchResult(BaseModel):
    """Result from resume-job matching"""
    resume_id: str = Field(..., description="Resume identifier")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    match_quality: str = Field(..., description="Match quality assessment")
    recommendation: str = Field(..., description="Recommendation text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Resume metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "resume_id": "resume_456",
                "similarity_score": 0.85,
                "match_quality": "Very Good",
                "recommendation": "Recommend - Very good match",
                "metadata": {
                    "user_id": "user_789",
                    "experience_years": 5,
                    "skills": ["Python", "React", "AWS"]
                }
            }
        }

class ResumeMatchResponse(BaseModel):
    """Response from resume-job matching"""
    job_length: int = Field(..., description="Length of job description")
    total_matches: int = Field(..., description="Total number of matches found")
    matches: List[ResumeMatchResult] = Field(default_factory=list, description="Resume matches")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")

class VectorDeleteRequest(BaseModel):
    """Request for deleting vectors"""
    vector_id: str = Field(..., description="Vector identifier to delete")
    index_type: IndexType = Field(..., description="Index type containing the vector")

class VectorBatchDeleteRequest(BaseModel):
    """Request for batch deleting vectors"""
    vector_ids: List[str] = Field(..., min_items=1, max_items=100, description="Vector IDs to delete")
    index_type: IndexType = Field(..., description="Index type containing the vectors")
    
    @validator('vector_ids')
    def validate_vector_ids(cls, v):
        if len(v) > 100:
            raise ValueError('Cannot delete more than 100 vectors at once')
        return v

class IndexStatsResponse(BaseModel):
    """Response with Pinecone index statistics"""
    index_name: str = Field(..., description="Index name")
    total_vector_count: int = Field(..., description="Total number of vectors")
    dimension: int = Field(..., description="Vector dimension")
    index_fullness: float = Field(..., ge=0.0, le=1.0, description="Index fullness percentage")
    namespaces: Dict[str, int] = Field(default_factory=dict, description="Namespace statistics")
    
    class Config:
        schema_extra = {
            "example": {
                "index_name": "resumes-index",
                "total_vector_count": 15420,
                "dimension": 1536,
                "index_fullness": 0.15,
                "namespaces": {
                    "default": 15420
                }
            }
        }

class VectorOperationResponse(BaseModel):
    """Response for vector operations (upsert, delete)"""
    operation: str = Field(..., description="Operation type")
    success: bool = Field(..., description="Operation success status")
    affected_count: int = Field(..., description="Number of vectors affected")
    details: Dict[str, Any] = Field(default_factory=dict, description="Operation details")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    
    class Config:
        schema_extra = {
            "example": {
                "operation": "upsert",
                "success": True,
                "affected_count": 1,
                "details": {"content_id": "resume_123"},
                "processing_time_ms": 456.78
            }
        }

class VectorBatchOperationResponse(BaseModel):
    """Response for batch vector operations"""
    operation: str = Field(..., description="Operation type")
    total_processed: int = Field(..., description="Total items processed")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    results: Dict[str, bool] = Field(..., description="Individual operation results")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    
    class Config:
        schema_extra = {
            "example": {
                "operation": "batch_upsert",
                "total_processed": 10,
                "successful": 9,
                "failed": 1,
                "results": {
                    "resume_1": True,
                    "resume_2": True,
                    "resume_3": False
                },
                "processing_time_ms": 2345.67
            }
        }
