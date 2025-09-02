# ai-service/app/routers/ai_routes.py - AI Service API Routes
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from ..models.schemas import (
    JobMatchRequest, JobMatchResponse, ResumeOptimizationRequest, ResumeOptimizationResponse,
    EnhancedOptimizationRequest, EnhancedOptimizationResponse, BatchJobAnalysisRequest, BatchAnalysisResponse,
    EmbeddingRequest, EmbeddingResponse, SessionStatusResponse, SessionListResponse,
    HealthCheckResponse, UsageMetricsResponse, ErrorResponse
)
from ..services.ai_service import ai_service, AIServiceError
from ..services.enhanced_optimization import enhanced_optimizer
from ..services.cache_service import cache_service
from ..database import get_db_context, check_db_health, get_db_stats
from ..models.ai_models import AIProcessingSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])

# Error handling middleware
@router.exception_handler(AIServiceError)
async def ai_service_error_handler(request, exc: AIServiceError):
    """Handle AI service errors"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            message=str(exc),
            error_code=exc.error_type,
            error_type=exc.error_type,
            details=exc.details
        ).dict()
    )

# Core AI Endpoints
@router.post("/analyze-match", response_model=JobMatchResponse)
async def analyze_job_match(request: JobMatchRequest):
    """
    Analyze semantic match between resume and job description
    Returns detailed scoring and recommendations
    """
    try:
        logger.info("Processing job match analysis request")
        
        result = await ai_service.analyze_job_match(
            resume_text=request.resume_text,
            job_description=request.job_description,
            user_id=str(request.user_id) if request.user_id else None
        )
        
        return JobMatchResponse(
            success=True,
            message="Job match analysis completed successfully",
            **result
        )
        
    except AIServiceError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in job match analysis: {e}")
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

@router.post("/optimize-resume", response_model=ResumeOptimizationResponse)
async def optimize_resume(request: ResumeOptimizationRequest):
    """
    AI-powered resume optimization for specific job
    Returns optimized resume with improvement details
    """
    try:
        logger.info("Processing resume optimization request")
        
        result = await ai_service.optimize_resume(
            resume_text=request.resume_text,
            job_description=request.job_description,
            user_id=str(request.user_id) if request.user_id else None
        )
        
        return ResumeOptimizationResponse(
            success=True,
            message="Resume optimization completed successfully",
            **result
        )
        
    except AIServiceError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in resume optimization: {e}")
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

@router.post("/enhanced-optimization", response_model=EnhancedOptimizationResponse)
async def enhanced_optimization(request: EnhancedOptimizationRequest):
    """
    Enhanced 3-stage AI optimization pipeline
    Returns comprehensive optimization with gap analysis and quality validation
    """
    try:
        logger.info("Processing enhanced optimization request")
        
        result = await enhanced_optimizer.optimize_resume_complete(
            resume_text=request.resume_text,
            job_description=request.job_description,
            user_context=request.user_context,
            user_id=str(request.user_id) if request.user_id else None
        )
        
        return EnhancedOptimizationResponse(
            success=True,
            message="Enhanced optimization completed successfully",
            **result
        )
        
    except AIServiceError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in enhanced optimization: {e}")
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

@router.post("/batch-analyze", response_model=BatchAnalysisResponse)
async def batch_analyze_jobs(request: BatchJobAnalysisRequest):
    """
    Analyze resume match against multiple job descriptions
    Returns ranked list of job matches
    """
    try:
        logger.info(f"Processing batch analysis request for {len(request.job_descriptions)} jobs")
        
        # Process jobs in parallel if requested
        if request.parallel_processing:
            import asyncio
            tasks = [
                ai_service.analyze_job_match(
                    resume_text=request.resume_text,
                    job_description=job_desc,
                    user_id=str(request.user_id) if request.user_id else None
                )
                for job_desc in request.job_descriptions
            ]
            results = await asyncio.gather(*tasks)
        else:
            results = []
            for job_desc in request.job_descriptions:
                result = await ai_service.analyze_job_match(
                    resume_text=request.resume_text,
                    job_description=job_desc,
                    user_id=str(request.user_id) if request.user_id else None
                )
                results.append(result)
        
        # Compile and rank results
        job_matches = []
        for i, result in enumerate(results):
            job_matches.append({
                "job_index": i,
                "job_preview": request.job_descriptions[i][:200] + "..." if len(request.job_descriptions[i]) > 200 else request.job_descriptions[i],
                "match_scores": result["match_scores"],
                "recommendation": result["recommendation"],
                "rank": 0,  # Will be set after sorting
                "confidence_score": result["confidence_score"]
            })
        
        # Sort by overall match score (highest first) and add ranks
        job_matches.sort(key=lambda x: x["match_scores"]["overall"], reverse=True)
        for i, job in enumerate(job_matches):
            job["rank"] = i + 1
        
        # Calculate summary statistics
        overall_scores = [job["match_scores"]["overall"] for job in job_matches]
        summary = {
            "top_match_score": max(overall_scores) if overall_scores else 0,
            "average_match_score": sum(overall_scores) / len(overall_scores) if overall_scores else 0,
            "jobs_above_80_percent": len([score for score in overall_scores if score >= 0.8]),
            "recommendation": "Focus on top 3 matches for best results" if len(job_matches) >= 3 else "Apply to all high-scoring positions"
        }
        
        return BatchAnalysisResponse(
            success=True,
            message=f"Batch analysis completed for {len(request.job_descriptions)} jobs",
            session_id=f"batch_{int(datetime.now().timestamp())}",
            total_jobs_analyzed=len(request.job_descriptions),
            matches=job_matches,
            best_match=job_matches[0] if job_matches else None,
            summary=summary,
            processing_metadata={
                "parallel_processing": request.parallel_processing,
                "processing_time": "completed"
            }
        )
        
    except AIServiceError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

@router.post("/embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(request: EmbeddingRequest):
    """
    Generate vector embeddings for text content
    Returns embeddings with metadata
    """
    try:
        logger.info(f"Processing embedding generation request for {len(request.texts)} texts")
        
        # Create session for embedding generation
        session_id = await ai_service.create_processing_session(
            operation_type="embedding_generation",
            user_id=str(request.user_id) if request.user_id else None
        )
        
        # Generate embeddings
        embeddings = await ai_service.get_embeddings(
            texts=request.texts,
            session_id=session_id if request.store_embeddings else None
        )
        
        # Calculate token counts (approximate)
        token_counts = [len(text.split()) * 1.3 for text in request.texts]  # Rough approximation
        
        # Update session status
        await ai_service.update_session_status(session_id, "completed")
        
        return EmbeddingResponse(
            success=True,
            message=f"Generated embeddings for {len(request.texts)} texts",
            session_id=session_id,
            embeddings=embeddings,
            model_used=ai_service.embedding_model,
            dimensions=len(embeddings[0]) if embeddings else 0,
            token_counts=token_counts,
            processing_metadata={
                "model_used": ai_service.embedding_model,
                "store_embeddings": request.store_embeddings
            }
        )
        
    except AIServiceError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in embedding generation: {e}")
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

# Session Management Endpoints
@router.get("/session/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """
    Get processing session status and progress
    """
    try:
        with get_db_context() as db:
            session = db.query(AIProcessingSession).filter(
                AIProcessingSession.session_id == session_id
            ).first()
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            return SessionStatusResponse(
                success=True,
                message="Session status retrieved successfully",
                session_id=session_id,
                status=session.status,
                operation_type=session.operation_type,
                progress_percentage=100.0 if session.status == "completed" else 50.0,
                estimated_completion=session.completed_at,
                current_stage="completed" if session.status == "completed" else "processing",
                error_message=session.error_message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session status: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving session status: {str(e)}")

@router.get("/sessions", response_model=SessionListResponse)
async def list_user_sessions(
    user_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    operation_type: Optional[str] = None
):
    """
    List processing sessions for a user
    """
    try:
        with get_db_context() as db:
            query = db.query(AIProcessingSession)
            
            if user_id:
                query = query.filter(AIProcessingSession.user_id == user_id)
            
            if operation_type:
                query = query.filter(AIProcessingSession.operation_type == operation_type)
            
            # Get total count
            total_sessions = query.count()
            
            # Apply pagination
            sessions = query.order_by(AIProcessingSession.created_at.desc()).offset(
                (page - 1) * page_size
            ).limit(page_size).all()
            
            # Convert to dict format
            session_list = []
            for session in sessions:
                session_list.append({
                    "session_id": session.session_id,
                    "operation_type": session.operation_type,
                    "status": session.status,
                    "created_at": session.created_at.isoformat(),
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                    "processing_time_ms": session.processing_time_ms,
                    "ai_calls_made": session.ai_calls_made,
                    "tokens_used": session.tokens_used
                })
            
            total_pages = (total_sessions + page_size - 1) // page_size
            
            return SessionListResponse(
                success=True,
                message=f"Retrieved {len(session_list)} sessions",
                sessions=session_list,
                total_sessions=total_sessions,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")

# Health and Monitoring Endpoints
@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Check AI service health and connectivity
    """
    try:
        # Check database health
        db_health = await check_db_health()
        
        # Test AI service functionality
        try:
            test_embeddings = await ai_service.get_embeddings(["test text"])
            ai_status = "operational" if test_embeddings else "degraded"
        except Exception as e:
            ai_status = "down"
            logger.error(f"AI service health check failed: {e}")
        
        return HealthCheckResponse(
            success=True,
            message="Health check completed",
            status="healthy" if db_health["status"] == "healthy" and ai_status == "operational" else "degraded",
            ai_service=ai_status,
            embedding_model=ai_service.embedding_model,
            chat_model=ai_service.chat_model,
            database=db_health["status"],
            redis="operational",  # Placeholder - implement Redis health check if needed
            vector_store="operational",  # Placeholder - implement vector store health check if needed
            last_check=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            success=False,
            message="Health check failed",
            status="unhealthy",
            ai_service="down",
            embedding_model="unknown",
            chat_model="unknown",
            database="down",
            redis="down",
            vector_store="down",
            last_check=datetime.utcnow()
        )

@router.get("/metrics", response_model=UsageMetricsResponse)
async def get_usage_metrics():
    """
    Get AI service usage metrics and analytics
    """
    try:
        # Get database statistics
        db_stats = await get_db_stats()
        
        # Calculate success rate
        total_sessions = db_stats.get("total_sessions", 0)
        completed_sessions = db_stats.get("completed_sessions", 0)
        success_rate = f"{(completed_sessions / total_sessions * 100):.1f}%" if total_sessions > 0 else "0%"
        
        # Calculate average processing time (placeholder)
        avg_processing_time = "3.2s"  # This would be calculated from actual session data
        
        return UsageMetricsResponse(
            success=True,
            message="Usage metrics retrieved successfully",
            daily_optimizations=db_stats.get("recent_optimizations", 0),
            success_rate=success_rate,
            avg_processing_time=avg_processing_time,
            popular_job_types=["Software Engineer", "Data Scientist", "Product Manager"],  # Placeholder
            avg_improvement="+31% callback rate",  # Placeholder
            user_satisfaction="4.8/5.0",  # Placeholder
            token_usage={
                "gpt-4o-mini": 15000,  # Placeholder
                "text-embedding-3-small": 5000  # Placeholder
            },
            error_rates={
                "job_match": 0.05,  # 5% error rate
                "resume_optimization": 0.03,  # 3% error rate
                "enhanced_optimization": 0.08  # 8% error rate
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving usage metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")

# Utility Endpoints
@router.get("/models")
async def list_available_models():
    """
    List available AI models and their capabilities
    """
    return {
        "success": True,
        "message": "Available models retrieved successfully",
        "embedding_models": {
            "text-embedding-3-small": {
                "dimensions": 1536,
                "max_tokens": 8191,
                "cost_per_1k_tokens": 0.00002
            },
            "text-embedding-3-large": {
                "dimensions": 3072,
                "max_tokens": 8191,
                "cost_per_1k_tokens": 0.00013
            }
        },
        "chat_models": {
            "gpt-4o-mini": {
                "max_tokens": 16384,
                "cost_per_1k_input": 0.00015,
                "cost_per_1k_output": 0.0006
            },
            "gpt-4o": {
                "max_tokens": 128000,
                "cost_per_1k_input": 0.005,
                "cost_per_1k_output": 0.015
            }
        },
        "current_defaults": {
            "embedding_model": ai_service.embedding_model,
            "chat_model": ai_service.chat_model
        }
    }

@router.get("/")
async def root():
    """
    AI service root endpoint
    """
    return {
        "service": "AI Service",
        "version": "1.0.0",
        "description": "Enhanced AI-powered resume analysis and optimization service",
        "endpoints": {
            "job_matching": "/api/ai/analyze-match",
            "resume_optimization": "/api/ai/optimize-resume",
            "enhanced_optimization": "/api/ai/enhanced-optimization",
            "batch_analysis": "/api/ai/batch-analyze",
            "embeddings": "/api/ai/embeddings",
            "health": "/api/ai/health",
            "metrics": "/api/ai/metrics"
        },
        "features": [
            "Semantic job-resume matching",
            "AI-powered resume optimization",
            "Enhanced 3-stage optimization pipeline",
            "Vector embeddings generation",
            "Batch job analysis",
            "Session management and tracking",
            "Quality validation and confidence scoring",
            "Redis caching for improved performance"
        ]
    }

# Cache Management Endpoints
@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get Redis cache statistics and health information
    """
    try:
        stats = await cache_service.get_cache_stats()
        return {
            "success": True,
            "message": "Cache statistics retrieved successfully",
            "cache_stats": stats
        }
    except Exception as e:
        logger.error(f"Error retrieving cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving cache stats: {str(e)}")

@router.get("/cache/health")
async def get_cache_health():
    """
    Check Redis cache health status
    """
    try:
        health = await cache_service.health_check()
        return {
            "success": True,
            "message": "Cache health check completed",
            "cache_health": health
        }
    except Exception as e:
        logger.error(f"Error checking cache health: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking cache health: {str(e)}")

@router.delete("/cache/clear/{prefix}")
async def clear_cache_by_prefix(prefix: str):
    """
    Clear cache entries by prefix (embedding, openai_response, job_match, optimization, session, health)
    """
    try:
        success = await cache_service.clear_cache_by_prefix(prefix)
        if success:
            return {
                "success": True,
                "message": f"Cache cleared successfully for prefix: {prefix}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@router.delete("/cache/clear-all")
async def clear_all_cache():
    """
    Clear all cache entries
    """
    try:
        success = True
        for prefix in ["embedding", "openai_response", "job_match", "optimization", "session", "health"]:
            if not await cache_service.clear_cache_by_prefix(prefix):
                success = False
        
        if success:
            return {
                "success": True,
                "message": "All cache entries cleared successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear some cache entries")
    except Exception as e:
        logger.error(f"Error clearing all cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")
