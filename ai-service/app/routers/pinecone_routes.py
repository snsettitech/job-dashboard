# ai-service/app/routers/pinecone_routes.py
"""
Pinecone Vector Database API Routes
Provides endpoints for semantic search and job matching using Pinecone
"""

import time
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

from ..services.pinecone_service import pinecone_service, IndexType
from ..models.schemas import (
    VectorSearchRequest, VectorSearchResponse, SearchResult,
    VectorUpsertRequest, VectorBatchUpsertRequest, VectorOperationResponse, VectorBatchOperationResponse,
    JobMatchRequest, JobMatchResponse, JobMatchResult,
    ResumeMatchRequest, ResumeMatchResponse, ResumeMatchResult,
    VectorDeleteRequest, VectorBatchDeleteRequest,
    IndexStatsResponse
)
from ..models.ai_models import AIProcessingSession, ProcessingStatus
from ..database import get_db_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pinecone", tags=["Pinecone Vector Database"])

@router.post("/search", response_model=VectorSearchResponse)
async def search_vectors(request: VectorSearchRequest):
    """
    Search for similar vectors using semantic similarity
    """
    start_time = time.time()
    
    try:
        # Perform search based on index type
        if request.index_type == IndexType.RESUMES:
            results = await pinecone_service.search_similar_resumes(
                query_text=request.query_text,
                top_k=request.top_k,
                filter_metadata=request.filter_metadata
            )
        elif request.index_type == IndexType.JOBS:
            results = await pinecone_service.search_similar_jobs(
                query_text=request.query_text,
                top_k=request.top_k,
                filter_metadata=request.filter_metadata
            )
        else:
            raise HTTPException(status_code=400, detail=f"Search not supported for index type: {request.index_type}")
        
        # Convert to response format
        search_results = []
        for result in results:
            search_result = SearchResult(
                content_id=result.content_id,
                content_type=result.content_type,
                similarity_score=result.similarity_score,
                metadata=result.metadata,
                content_preview=result.content_preview
            )
            search_results.append(search_result)
        
        search_time = (time.time() - start_time) * 1000
        
        return VectorSearchResponse(
            query_text=request.query_text,
            index_type=request.index_type,
            results=search_results,
            total_results=len(search_results),
            search_time_ms=search_time
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search operation failed: {str(e)}")

@router.post("/upsert", response_model=VectorOperationResponse)
async def upsert_vector(request: VectorUpsertRequest):
    """
    Upsert a single vector to Pinecone
    """
    start_time = time.time()
    
    try:
        # Determine index type based on content type
        index_type = None
        if request.content_type == "resume":
            index_type = IndexType.RESUMES
        elif request.content_type == "job":
            index_type = IndexType.JOBS
        elif request.content_type == "skill":
            index_type = IndexType.SKILLS
        elif request.content_type == "company":
            index_type = IndexType.COMPANIES
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported content type: {request.content_type}")
        
        # Perform upsert
        success = False
        if index_type == IndexType.RESUMES:
            success = await pinecone_service.upsert_resume(
                resume_id=request.content_id,
                resume_text=request.content_text,
                user_id=request.user_id,
                session_id=request.session_id,
                metadata=request.metadata
            )
        elif index_type == IndexType.JOBS:
            success = await pinecone_service.upsert_job(
                job_id=request.content_id,
                job_description=request.content_text,
                job_metadata=request.metadata,
                session_id=request.session_id
            )
        else:
            # For skills and companies, use generic upsert
            success = await pinecone_service.upsert_job(
                job_id=request.content_id,
                job_description=request.content_text,
                job_metadata=request.metadata,
                session_id=request.session_id
            )
        
        processing_time = (time.time() - start_time) * 1000
        
        return VectorOperationResponse(
            operation="upsert",
            success=success,
            affected_count=1 if success else 0,
            details={"content_id": request.content_id, "content_type": request.content_type},
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Upsert failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upsert operation failed: {str(e)}")

@router.post("/batch-upsert", response_model=VectorBatchOperationResponse)
async def batch_upsert_vectors(request: VectorBatchUpsertRequest):
    """
    Batch upsert multiple vectors to Pinecone
    """
    start_time = time.time()
    
    try:
        # Group vectors by type
        resumes = []
        jobs = []
        
        for vector in request.vectors:
            if vector.content_type == "resume":
                resumes.append({
                    'id': vector.content_id,
                    'text': vector.content_text,
                    'user_id': vector.user_id,
                    'metadata': vector.metadata or {}
                })
            elif vector.content_type == "job":
                jobs.append({
                    'id': vector.content_id,
                    'description': vector.content_text,
                    'metadata': vector.metadata or {}
                })
        
        # Perform batch operations
        results = {}
        
        if resumes:
            resume_results = await pinecone_service.batch_upsert_resumes(resumes)
            results.update(resume_results)
        
        if jobs:
            job_results = await pinecone_service.batch_upsert_jobs(jobs)
            results.update(job_results)
        
        # Calculate statistics
        total_processed = len(results)
        successful = sum(1 for success in results.values() if success)
        failed = total_processed - successful
        
        processing_time = (time.time() - start_time) * 1000
        
        return VectorBatchOperationResponse(
            operation="batch_upsert",
            total_processed=total_processed,
            successful=successful,
            failed=failed,
            results=results,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Batch upsert failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch upsert operation failed: {str(e)}")

@router.post("/match-resume-to-jobs", response_model=JobMatchResponse)
async def match_resume_to_jobs(request: JobMatchRequest):
    """
    Match a resume to similar jobs using semantic similarity
    """
    start_time = time.time()
    
    try:
        # Perform matching
        matches = await pinecone_service.match_resume_to_jobs(
            resume_text=request.resume_text,
            job_ids=request.job_ids,
            top_k=request.top_k,
            min_similarity=request.min_similarity
        )
        
        # Convert to response format
        job_matches = []
        for match in matches:
            job_match = JobMatchResult(
                job_id=match['job_id'],
                similarity_score=match['similarity_score'],
                match_quality=match['match_quality'],
                recommendation=match['recommendation'],
                metadata=match['metadata']
            )
            job_matches.append(job_match)
        
        processing_time = (time.time() - start_time) * 1000
        
        return JobMatchResponse(
            resume_length=len(request.resume_text),
            total_matches=len(job_matches),
            matches=job_matches,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Resume to jobs matching failed: {e}")
        raise HTTPException(status_code=500, detail=f"Matching operation failed: {str(e)}")

@router.post("/match-jobs-to-resume", response_model=ResumeMatchResponse)
async def match_jobs_to_resume(request: ResumeMatchRequest):
    """
    Match a job to similar resumes using semantic similarity
    """
    start_time = time.time()
    
    try:
        # Perform matching
        matches = await pinecone_service.match_jobs_to_resume(
            job_description=request.job_description,
            resume_ids=request.resume_ids,
            top_k=request.top_k,
            min_similarity=request.min_similarity
        )
        
        # Convert to response format
        resume_matches = []
        for match in matches:
            resume_match = ResumeMatchResult(
                resume_id=match['resume_id'],
                similarity_score=match['similarity_score'],
                match_quality=match['match_quality'],
                recommendation=match['recommendation'],
                metadata=match['metadata']
            )
            resume_matches.append(resume_match)
        
        processing_time = (time.time() - start_time) * 1000
        
        return ResumeMatchResponse(
            job_length=len(request.job_description),
            total_matches=len(resume_matches),
            matches=resume_matches,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Jobs to resume matching failed: {e}")
        raise HTTPException(status_code=500, detail=f"Matching operation failed: {str(e)}")

@router.delete("/delete", response_model=VectorOperationResponse)
async def delete_vector(request: VectorDeleteRequest):
    """
    Delete a vector from Pinecone
    """
    start_time = time.time()
    
    try:
        success = await pinecone_service.delete_vector(
            vector_id=request.vector_id,
            index_type=request.index_type
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return VectorOperationResponse(
            operation="delete",
            success=success,
            affected_count=1 if success else 0,
            details={"vector_id": request.vector_id, "index_type": request.index_type.value},
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delete operation failed: {str(e)}")

@router.delete("/batch-delete", response_model=VectorBatchOperationResponse)
async def batch_delete_vectors(request: VectorBatchDeleteRequest):
    """
    Batch delete multiple vectors from Pinecone
    """
    start_time = time.time()
    
    try:
        results = {}
        for vector_id in request.vector_ids:
            success = await pinecone_service.delete_vector(
                vector_id=vector_id,
                index_type=request.index_type
            )
            results[vector_id] = success
        
        # Calculate statistics
        total_processed = len(results)
        successful = sum(1 for success in results.values() if success)
        failed = total_processed - successful
        
        processing_time = (time.time() - start_time) * 1000
        
        return VectorBatchOperationResponse(
            operation="batch_delete",
            total_processed=total_processed,
            successful=successful,
            failed=failed,
            results=results,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Batch delete failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch delete operation failed: {str(e)}")

@router.get("/stats/{index_type}", response_model=IndexStatsResponse)
async def get_index_stats(index_type: IndexType):
    """
    Get statistics for a Pinecone index
    """
    try:
        stats = await pinecone_service.get_index_stats(index_type)
        
        if not stats:
            raise HTTPException(status_code=404, detail=f"Index stats not found for {index_type}")
        
        return IndexStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get index stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get index stats: {str(e)}")

@router.get("/health")
async def pinecone_health_check():
    """
    Health check for Pinecone service
    """
    try:
        # Check if Pinecone is initialized
        if not pinecone_service.api_key:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "message": "Pinecone API key not configured",
                    "service": "pinecone"
                }
            )
        
        # Try to get stats from resumes index as a health check
        stats = await pinecone_service.get_index_stats(IndexType.RESUMES)
        
        return {
            "status": "healthy",
            "message": "Pinecone service is operational",
            "service": "pinecone",
            "index_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Pinecone health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "message": f"Pinecone service error: {str(e)}",
                "service": "pinecone"
            }
        )

@router.get("/indexes")
async def list_indexes():
    """
    List all available Pinecone indexes
    """
    try:
        indexes = []
        for index_type in IndexType:
            stats = await pinecone_service.get_index_stats(index_type)
            if stats:
                indexes.append({
                    "index_type": index_type.value,
                    "index_name": stats.get("index_name"),
                    "total_vectors": stats.get("total_vector_count", 0),
                    "dimension": stats.get("dimension"),
                    "fullness": stats.get("index_fullness", 0.0)
                })
        
        return {
            "indexes": indexes,
            "total_indexes": len(indexes)
        }
        
    except Exception as e:
        logger.error(f"Failed to list indexes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list indexes: {str(e)}")

@router.post("/sync-from-database")
async def sync_from_database(background_tasks: BackgroundTasks):
    """
    Sync vectors from local database to Pinecone (background task)
    """
    try:
        # This would be implemented to sync existing embeddings from PostgreSQL to Pinecone
        # For now, return a placeholder response
        background_tasks.add_task(_sync_embeddings_background)
        
        return {
            "message": "Database sync started in background",
            "task": "sync_embeddings"
        }
        
    except Exception as e:
        logger.error(f"Failed to start database sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start database sync: {str(e)}")

async def _sync_embeddings_background():
    """
    Background task to sync embeddings from database to Pinecone
    """
    try:
        with get_db_context() as db:
            # Get all embeddings from database
            embeddings = db.query(AIProcessingSession).all()
            
            # Sync to Pinecone (implementation would go here)
            logger.info(f"Syncing {len(embeddings)} embeddings to Pinecone")
            
    except Exception as e:
        logger.error(f"Background sync failed: {e}")

