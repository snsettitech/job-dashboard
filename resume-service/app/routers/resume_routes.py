# resume-service/app/routers/resume_routes.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from ..database import get_db
from ..models.schemas import (
    ResumeResponse, ResumeListResponse, ResumeUploadRequest, ResumeUploadResponse,
    ResumeUpdate, ResumeVersionResponse, ResumeVersionListResponse,
    ResumeOptimizationRequest, ResumeOptimizationResponse, ResumeOptimizationListResponse,
    ResumeAnalysisRequest, ResumeAnalysisResponse, ResumeAnalysisListResponse,
    BaseResponse, ErrorResponse, ProcessingStatusResponse, ServiceHealth
)
from ..models.resume_models import Resume, ResumeVersion, ResumeOptimization, ResumeAnalysis
from ..services.resume_service import ResumeService
from ..services.storage_service import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resumes", tags=["Resume Management"])

# Initialize services
resume_service = ResumeService()
storage_service = StorageService()

# Resume Management Routes
@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    is_public: bool = Form(default=False),
    db: Session = Depends(get_db)
):
    """Upload a new resume file"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size (10MB limit)
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 10MB")
        
        # Determine file type
        file_type = file.filename.split('.')[-1].lower()
        if file_type not in ['pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png']:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Create resume upload request
        from ..models.schemas import ResumeCreate, FileType, StorageProvider
        resume_data = ResumeCreate(
            user_id=user_id,
            filename=file.filename,
            file_type=FileType(file_type),
            file_size=len(file_content),
            mime_type=file.content_type or "application/octet-stream",
            is_public=is_public
        )
        
        # Create resume
        resume = await resume_service.create_resume(db, resume_data, file_content)
        
        return ResumeUploadResponse(
            resume_id=resume.id,
            upload_url=resume.storage_url,
            storage_key=resume.storage_key,
            expires_at=datetime.utcnow(),
            status="completed"
        )
        
    except Exception as e:
        logger.error(f"Failed to upload resume: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/", response_model=ResumeListResponse)
async def list_resumes(
    user_id: str = Query(..., description="User ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all resumes for a user"""
    try:
        resumes = resume_service.get_user_resumes(db, user_id, skip, limit)
        
        return ResumeListResponse(
            resumes=[ResumeResponse.from_orm(resume) for resume in resumes],
            total_count=len(resumes),
            page=skip // limit + 1,
            page_size=limit,
            total_pages=(len(resumes) + limit - 1) // limit
        )
        
    except Exception as e:
        logger.error(f"Failed to list resumes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list resumes: {str(e)}")

@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get a specific resume by ID"""
    try:
        resume = resume_service.get_resume(db, resume_id, user_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        return ResumeResponse.from_orm(resume)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get resume: {str(e)}")

@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: str,
    update_data: ResumeUpdate,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Update resume information"""
    try:
        resume = resume_service.update_resume(db, resume_id, user_id, update_data)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        return ResumeResponse.from_orm(resume)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update resume: {str(e)}")

@router.delete("/{resume_id}", response_model=BaseResponse)
async def delete_resume(
    resume_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Delete a resume"""
    try:
        success = await resume_service.delete_resume(db, resume_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        return BaseResponse(
            message=f"Resume {resume_id} deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete resume {resume_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete resume: {str(e)}")

# Resume Version Routes
@router.post("/{resume_id}/versions", response_model=ResumeVersionResponse)
async def create_resume_version(
    resume_id: str,
    file: UploadFile = File(...),
    user_id: str = Form(...),
    version_reason: str = Form(default="manual_edit"),
    db: Session = Depends(get_db)
):
    """Create a new version of a resume"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 10MB")
        
        # Create version
        version = await resume_service.create_resume_version(
            db, resume_id, user_id, file_content, file.filename, version_reason
        )
        
        if not version:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        return ResumeVersionResponse.from_orm(version)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create resume version: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create version: {str(e)}")

@router.get("/{resume_id}/versions", response_model=ResumeVersionListResponse)
async def list_resume_versions(
    resume_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get all versions of a resume"""
    try:
        versions = resume_service.get_resume_versions(db, resume_id, user_id)
        
        return ResumeVersionListResponse(
            versions=[ResumeVersionResponse.from_orm(version) for version in versions],
            total_count=len(versions),
            resume_id=resume_id
        )
        
    except Exception as e:
        logger.error(f"Failed to list resume versions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list versions: {str(e)}")

# Resume Optimization Routes
@router.post("/{resume_id}/optimize", response_model=ResumeOptimizationResponse)
async def create_resume_optimization(
    resume_id: str,
    optimization_data: ResumeOptimizationRequest,
    user_id: str = Query(..., description="User ID"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Create a resume optimization request"""
    try:
        # Set resume_id from URL
        optimization_data.resume_id = resume_id
        
        # Create optimization request
        optimization = await resume_service.create_resume_optimization(db, optimization_data, user_id)
        
        if not optimization:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Add background task to process optimization
        if background_tasks:
            background_tasks.add_task(
                resume_service.process_resume_optimization, db, optimization.id
            )
        
        return ResumeOptimizationResponse.from_orm(optimization)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create optimization: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create optimization: {str(e)}")

@router.get("/{resume_id}/optimizations", response_model=ResumeOptimizationListResponse)
async def list_resume_optimizations(
    resume_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get all optimizations for a resume"""
    try:
        optimizations = resume_service.get_resume_optimizations(db, resume_id, user_id)
        
        return ResumeOptimizationListResponse(
            optimizations=[ResumeOptimizationResponse.from_orm(opt) for opt in optimizations],
            total_count=len(optimizations),
            resume_id=resume_id
        )
        
    except Exception as e:
        logger.error(f"Failed to list optimizations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list optimizations: {str(e)}")

@router.get("/optimizations/{optimization_id}", response_model=ResumeOptimizationResponse)
async def get_optimization(
    optimization_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get a specific optimization by ID"""
    try:
        optimization = db.query(ResumeOptimization).filter(
            ResumeOptimization.id == optimization_id
        ).first()
        
        if not optimization:
            raise HTTPException(status_code=404, detail="Optimization not found")
        
        # Verify user owns the resume
        resume = resume_service.get_resume(db, optimization.resume_id, user_id)
        if not resume:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return ResumeOptimizationResponse.from_orm(optimization)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get optimization {optimization_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get optimization: {str(e)}")

# Resume Analysis Routes
@router.post("/{resume_id}/analyze", response_model=ResumeAnalysisResponse)
async def create_resume_analysis(
    resume_id: str,
    analysis_data: ResumeAnalysisRequest,
    user_id: str = Query(..., description="User ID"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Create a resume analysis request"""
    try:
        # Set resume_id from URL
        analysis_data.resume_id = resume_id
        
        # Create analysis request
        analysis = await resume_service.create_resume_analysis(db, analysis_data, user_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Add background task to process analysis
        if background_tasks:
            background_tasks.add_task(
                resume_service.process_resume_analysis, db, analysis.id
            )
        
        return ResumeAnalysisResponse.from_orm(analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create analysis: {str(e)}")

@router.get("/{resume_id}/analyses", response_model=ResumeAnalysisListResponse)
async def list_resume_analyses(
    resume_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get all analyses for a resume"""
    try:
        analyses = resume_service.get_resume_analyses(db, resume_id, user_id)
        
        return ResumeAnalysisListResponse(
            analyses=[ResumeAnalysisResponse.from_orm(analysis) for analysis in analyses],
            total_count=len(analyses),
            resume_id=resume_id
        )
        
    except Exception as e:
        logger.error(f"Failed to list analyses: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list analyses: {str(e)}")

@router.get("/analyses/{analysis_id}", response_model=ResumeAnalysisResponse)
async def get_analysis(
    analysis_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get a specific analysis by ID"""
    try:
        analysis = db.query(ResumeAnalysis).filter(
            ResumeAnalysis.id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Verify user owns the resume
        resume = resume_service.get_resume(db, analysis.resume_id, user_id)
        if not resume:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return ResumeAnalysisResponse.from_orm(analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")

# Processing Status Routes
@router.get("/{resume_id}/status", response_model=ProcessingStatusResponse)
async def get_processing_status(
    resume_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get processing status for a resume"""
    try:
        resume = resume_service.get_resume(db, resume_id, user_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        return ProcessingStatusResponse(
            resume_id=resume_id,
            status=resume.processing_status,
            error_message=resume.processing_error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processing status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

# Statistics Routes
@router.get("/stats/user/{user_id}")
async def get_user_resume_stats(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get resume statistics for a user"""
    try:
        stats = resume_service.get_user_resume_stats(db, user_id)
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

# File Download Routes
@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Download resume file"""
    try:
        resume = resume_service.get_resume(db, resume_id, user_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Generate presigned URL for download
        download_url = storage_service.generate_presigned_url(resume.storage_key, expiration=3600)
        
        return {
            "download_url": download_url,
            "filename": resume.filename,
            "expires_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")

@router.get("/{resume_id}/versions/{version_id}/download")
async def download_resume_version(
    resume_id: str,
    version_id: str,
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Download a specific resume version"""
    try:
        # Verify user owns the resume
        resume = resume_service.get_resume(db, resume_id, user_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Get version
        version = db.query(ResumeVersion).filter(
            ResumeVersion.id == version_id,
            ResumeVersion.resume_id == resume_id
        ).first()
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        # Generate presigned URL for download
        download_url = storage_service.generate_presigned_url(version.storage_key, expiration=3600)
        
        return {
            "download_url": download_url,
            "filename": version.filename,
            "version_number": version.version_number,
            "expires_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate version download URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate download URL: {str(e)}")



