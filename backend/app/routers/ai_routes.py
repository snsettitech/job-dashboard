# backend/app/routers/ai_routes.py - Complete AI-Powered API Routes
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import json
import tempfile
import os
from datetime import datetime

from ..services.ai_service import analyze_job_match, optimize_resume, AIService
from ..services.file_processor import FileProcessor, validate_resume_quality

router = APIRouter(prefix="/api/ai", tags=["ai"])

# Request/Response Models
class JobMatchRequest(BaseModel):
    resume_text: str
    job_description: str

class JobMatchResponse(BaseModel):
    match_scores: dict
    recommendation: str
    analysis_date: str

class ResumeOptimizationRequest(BaseModel):
    resume_text: str
    job_description: str

class ResumeOptimizationResponse(BaseModel):
    optimized_resume: str
    improvements_made: List[str]
    keywords_added: List[str]
    ats_score_improvement: str
    optimization_date: str

@router.post("/analyze-match", response_model=JobMatchResponse)
async def analyze_resume_job_match(request: JobMatchRequest):
    """
    Analyze semantic match between resume and job description
    Returns detailed scoring and recommendations
    """
    try:
        if not request.resume_text.strip() or not request.job_description.strip():
            raise HTTPException(status_code=400, detail="Both resume text and job description are required")
        
        result = await analyze_job_match(request.resume_text, request.job_description)
        return JobMatchResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing job match: {str(e)}")

@router.post("/optimize-resume", response_model=ResumeOptimizationResponse)
async def optimize_resume_for_job(request: ResumeOptimizationRequest):
    """
    AI-powered resume optimization for specific job description
    Returns optimized resume with improvement details
    """
    try:
        if not request.resume_text.strip() or not request.job_description.strip():
            raise HTTPException(status_code=400, detail="Both resume text and job description are required")
        
        result = await optimize_resume(request.resume_text, request.job_description)
        return ResumeOptimizationResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing resume: {str(e)}")

@router.post("/upload-analyze-optimize")
async def upload_analyze_and_optimize_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    company_name: str = Form(default=""),
    job_title: str = Form(default="")
):
    """
    Complete resume processing pipeline:
    1. Upload and extract text from resume file
    2. Analyze match with job description
    3. Generate optimized version
    4. Return comprehensive analysis
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        max_file_size = 5 * 1024 * 1024  # 5MB
        file_content = await file.read()
        
        if len(file_content) > max_file_size:
            raise HTTPException(status_code=400, detail="File size must be less than 5MB")
        
        # Process file
        file_processor = FileProcessor()
        extracted_info = await file_processor.extract_text(
            file_content, 
            file.content_type, 
            file.filename
        )
        
        resume_text = extracted_info["cleaned_text"]
        
        if len(resume_text.split()) < 50:  # Minimum word count
            raise HTTPException(status_code=400, detail="Resume appears to be too short or text extraction failed")
        
        # Validate resume quality
        quality_analysis = validate_resume_quality(extracted_info)
        
        # Run AI analysis and optimization in parallel
        ai_service = AIService()
        
        # Analyze match
        match_task = ai_service.match_resume_to_job(resume_text, job_description)
        
        # Optimize resume
        optimize_task = ai_service.optimize_resume_for_job(
            resume_text, 
            job_description, 
            extracted_info["structured_info"]
        )
        
        # Execute both tasks concurrently
        match_scores, optimization_result = await asyncio.gather(match_task, optimize_task)
        
        # Compile comprehensive response
        response = {
            "status": "success",
            "processing_date": datetime.now().isoformat(),
            "file_info": extracted_info["metadata"],
            "original_resume": {
                "text": resume_text,
                "word_count": len(resume_text.split()),
                "quality_analysis": quality_analysis,
                "structured_info": extracted_info["structured_info"]
            },
            "job_match_analysis": {
                "scores": match_scores,
                "recommendation": _get_match_recommendation(match_scores["overall"]),
                "top_matching_skills": extracted_info["structured_info"]["skills"]["identified_skills"][:5]
            },
            "optimization": {
                **optimization_result,
                "improvement_summary": {
                    "original_words": len(resume_text.split()),
                    "optimized_words": len(optimization_result["optimized_resume"].split()),
                    "keywords_improvement": len(optimization_result.get("keywords_added", [])),
                    "estimated_callback_improvement": optimization_result.get("ats_score_improvement", "N/A")
                }
            },
            "next_steps": [
                "Review the optimized resume carefully",
                "Customize the resume further for specific companies",
                "Use the optimized version for applications",
                "Track application outcomes to measure improvement"
            ]
        }
        
        return JSONResponse(content=response)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@router.post("/download-optimized-resume")
async def download_optimized_resume(
    optimized_text: str = Form(...),
    filename: str = Form(default="optimized_resume.txt")
):
    """
    Create downloadable file with optimized resume
    """
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as temp_file:
            temp_file.write(optimized_text)
            temp_file_path = temp_file.name
        
        # Return file response
        return FileResponse(
            temp_file_path, 
            filename=filename,
            media_type='text/plain',
            background=BackgroundTasks().add_task(lambda: os.unlink(temp_file_path))
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating download file: {str(e)}")

@router.post("/batch-analyze-jobs")
async def batch_analyze_multiple_jobs(
    resume_text: str = Form(...),
    job_descriptions: str = Form(...)  # JSON string of job descriptions
):
    """
    Analyze resume match against multiple job descriptions
    Returns ranked list of job matches
    """
    try:
        # Parse job descriptions
        jobs = json.loads(job_descriptions)
        
        if not isinstance(jobs, list) or len(jobs) == 0:
            raise HTTPException(status_code=400, detail="job_descriptions must be a non-empty list")
        
        if len(jobs) > 10:  # Limit batch size
            raise HTTPException(status_code=400, detail="Maximum 10 jobs can be analyzed in a single batch")
        
        # Analyze each job concurrently for better performance
        ai_service = AIService()
        tasks = [ai_service.match_resume_to_job(resume_text, job_desc) for job_desc in jobs]
        results = await asyncio.gather(*tasks)
        
        # Add job index and compile results
        analyzed_jobs = []
        for i, result in enumerate(results):
            analyzed_jobs.append({
                "job_index": i,
                "job_preview": jobs[i][:200] + "..." if len(jobs[i]) > 200 else jobs[i],
                "match_scores": result,
                "recommendation": _get_match_recommendation(result["overall"]),
                "rank": 0  # Will be set after sorting
            })
        
        # Sort by match score (highest first) and add ranks
        analyzed_jobs.sort(key=lambda x: x["match_scores"]["overall"], reverse=True)
        
        for i, job in enumerate(analyzed_jobs):
            job["rank"] = i + 1
        
        return {
            "total_jobs_analyzed": len(jobs),
            "analysis_date": datetime.now().isoformat(),
            "matches": analyzed_jobs,
            "best_match": analyzed_jobs[0] if analyzed_jobs else None,
            "summary": {
                "top_match_score": analyzed_jobs[0]["match_scores"]["overall"] if analyzed_jobs else 0,
                "average_match_score": sum(job["match_scores"]["overall"] for job in analyzed_jobs) / len(analyzed_jobs) if analyzed_jobs else 0,
                "jobs_above_80_percent": len([job for job in analyzed_jobs if job["match_scores"]["overall"] >= 0.8]),
                "recommendation": "Focus on top 3 matches for best results" if len(analyzed_jobs) >= 3 else "Apply to all high-scoring positions"
            }
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for job_descriptions")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch analysis: {str(e)}")

@router.get("/health")
async def ai_health_check():
    """Check if AI services are working properly"""
    try:
        ai_service = AIService()
        
        # Test embedding generation
        test_embeddings = await ai_service.get_embeddings(["test text"])
        
        if not test_embeddings:
            raise Exception("Embedding generation failed")
        
        return {
            "status": "healthy",
            "ai_service": "operational",
            "embedding_model": ai_service.embedding_model,
            "chat_model": ai_service.chat_model,
            "test_embedding_dimensions": len(test_embeddings[0]) if test_embeddings else 0,
            "file_processing": "enabled",
            "supported_formats": ["PDF", "DOCX", "TXT"]
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "ai_service": "down"
        }

@router.get("/usage-stats")
async def get_ai_usage_stats():
    """Get AI service usage statistics (placeholder for production monitoring)"""
    return {
        "daily_optimizations": 47,
        "success_rate": "94%",
        "avg_processing_time": "3.2s",
        "popular_job_types": ["Software Engineer", "Data Scientist", "Product Manager"],
        "avg_improvement": "+31% callback rate",
        "user_satisfaction": "4.8/5.0"
    }

# Utility functions
def _get_match_recommendation(overall_score: float) -> str:
    """Generate recommendation based on match score"""
    if overall_score >= 0.9:
        return "🎯 Excellent match! This position aligns perfectly with your background. Apply immediately!"
    elif overall_score >= 0.8:
        return "🚀 Strong match! You should definitely apply to this position with confidence."
    elif overall_score >= 0.7:
        return "✨ Good match! Consider tailoring your resume for this role to increase your chances."
    elif overall_score >= 0.6:
        return "💡 Moderate match. Focus on highlighting relevant skills and consider optimization."
    else:
        return "🤔 Lower match. Consider if this aligns with your career goals or if significant optimization is needed."# backend/app/routers/ai_routes.py - AI-Powered API Routes
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import json

from ..services.ai_service import analyze_job_match, optimize_resume, AIService

router = APIRouter(prefix="/api/ai", tags=["ai"])

# Request/Response Models
class JobMatchRequest(BaseModel):
    resume_text: str
    job_description: str

class JobMatchResponse(BaseModel):
    match_scores: dict
    recommendation: str
    analysis_date: str

class ResumeOptimizationRequest(BaseModel):
    resume_text: str
    job_description: str

class ResumeOptimizationResponse(BaseModel):
    optimized_resume: str
    improvements_made: List[str]
    keywords_added: List[str]
    ats_score_improvement: str
    optimization_date: str

@router.post("/analyze-match", response_model=JobMatchResponse)
async def analyze_resume_job_match(request: JobMatchRequest):
    """
    Analyze semantic match between resume and job description
    Returns detailed scoring and recommendations
    """
    try:
        if not request.resume_text.strip() or not request.job_description.strip():
            raise HTTPException(status_code=400, detail="Both resume text and job description are required")
        
        result = await analyze_job_match(request.resume_text, request.job_description)
        return JobMatchResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing job match: {str(e)}")

@router.post("/optimize-resume", response_model=ResumeOptimizationResponse)
async def optimize_resume_for_job(request: ResumeOptimizationRequest):
    """
    AI-powered resume optimization for specific job description
    Returns optimized resume with improvement details
    """
    try:
        if not request.resume_text.strip() or not request.job_description.strip():
            raise HTTPException(status_code=400, detail="Both resume text and job description are required")
        
        result = await optimize_resume(request.resume_text, request.job_description)
        return ResumeOptimizationResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing resume: {str(e)}")

@router.post("/upload-resume-analyze")
async def upload_and_analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    """
    Upload resume file and analyze match with job description
    Supports PDF and DOCX files
    """
    try:
        # Validate file type
        if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]:
            raise HTTPException(status_code=400, detail="Only PDF, DOCX, and TXT files are supported")
        
        # Read file content
        content = await file.read()
        
        # Extract text from file (we'll implement this in Step 4)
        resume_text = await extract_text_from_file(content, file.content_type)
        
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from uploaded file")
        
        # Analyze match
        result = await analyze_job_match(resume_text, job_description)
        
        # Add file info to response
        result["file_info"] = {
            "filename": file.filename,
            "file_type": file.content_type,
            "file_size": len(content)
        }
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing uploaded resume: {str(e)}")

@router.post("/batch-analyze-jobs")
async def batch_analyze_multiple_jobs(
    resume_text: str = Form(...),
    job_descriptions: str = Form(...)  # JSON string of job descriptions
):
    """
    Analyze resume match against multiple job descriptions
    Returns ranked list of job matches
    """
    try:
        # Parse job descriptions
        jobs = json.loads(job_descriptions)
        
        if not isinstance(jobs, list) or len(jobs) == 0:
            raise HTTPException(status_code=400, detail="job_descriptions must be a non-empty list")
        
        # Analyze each job concurrently for better performance
        tasks = [analyze_job_match(resume_text, job_desc) for job_desc in jobs]
        results = await asyncio.gather(*tasks)
        
        # Add job index and sort by overall match score
        for i, result in enumerate(results):
            result["job_index"] = i
            result["job_description_preview"] = jobs[i][:200] + "..." if len(jobs[i]) > 200 else jobs[i]
        
        # Sort by match score (highest first)
        results.sort(key=lambda x: x["match_scores"]["overall"], reverse=True)
        
        return {
            "total_jobs_analyzed": len(jobs),
            "matches": results,
            "best_match": results[0] if results else None,
            "analysis_date": results[0]["analysis_date"] if results else None
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for job_descriptions")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch analysis: {str(e)}")

@router.get("/health")
async def ai_health_check():
    """Check if AI services are working properly"""
    try:
        ai_service = AIService()
        
        # Test embedding generation
        test_embeddings = await ai_service.get_embeddings(["test text"])
        
        if not test_embeddings:
            raise Exception("Embedding generation failed")
        
        return {
            "status": "healthy",
            "ai_service": "operational",
            "embedding_model": ai_service.embedding_model,
            "chat_model": ai_service.chat_model,
            "test_embedding_dimensions": len(test_embeddings[0]) if test_embeddings else 0
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "ai_service": "down"
        }

# Utility function for file text extraction (placeholder - implement in Step 4)
async def extract_text_from_file(content: bytes, content_type: str) -> str:
    """
    Extract text from uploaded files
    This will be implemented with PyMuPDF (PDF) and python-docx (DOCX)
    """
    if content_type == "text/plain":
        return content.decode("utf-8")
    elif content_type == "application/pdf":
        # TODO: Implement PDF extraction with PyMuPDF
        return "PDF extraction not yet implemented - please use plain text for now"
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        # TODO: Implement DOCX extraction with python-docx
        return "DOCX extraction not yet implemented - please use plain text for now"
    else:
        raise Exception(f"Unsupported file type: {content_type}")