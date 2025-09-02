# ai-service/app/services/enhanced_job_matching.py
"""
Enhanced Job Matching Service with Pinecone Integration
Combines semantic analysis with vector similarity search for optimal job matching
"""

import asyncio
import json
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import numpy as np
from dataclasses import dataclass

from ..models.schemas import JobMatchRequest, JobMatchResponse, JobMatchResult
from ..services.pinecone_service import pinecone_service, IndexType
from ..services.ai_service import ai_service
from ..database import get_db_context
from ..models.ai_models import JobMatchAnalysis, AIProcessingSession, ProcessingStatus

logger = logging.getLogger(__name__)

@dataclass
class MatchingConfig:
    """Configuration for job matching"""
    vector_similarity_weight: float = 0.6
    semantic_analysis_weight: float = 0.4
    min_combined_score: float = 0.7
    max_results: int = 20
    enable_advanced_filtering: bool = True
    enable_skill_extraction: bool = True
    enable_experience_matching: bool = True

class EnhancedJobMatcher:
    """
    Enhanced job matching service that combines Pinecone vector search with semantic analysis
    """
    
    def __init__(self, config: Optional[MatchingConfig] = None):
        self.config = config or MatchingConfig()
        self.ai_service = ai_service
        
    async def match_resume_to_jobs(self, request: JobMatchRequest) -> JobMatchResponse:
        """
        Enhanced job matching combining vector similarity and semantic analysis
        """
        start_time = datetime.utcnow()
        
        try:
            # Create processing session
            session_id = await self.ai_service.create_processing_session(
                operation_type="job_matching",
                user_id=request.user_id
            )
            
            # Step 1: Vector similarity search using Pinecone
            vector_matches = await self._perform_vector_search(request, session_id)
            
            # Step 2: Semantic analysis for top matches
            enhanced_matches = await self._enhance_with_semantic_analysis(
                request.resume_text, vector_matches, session_id
            )
            
            # Step 3: Apply advanced filtering and ranking
            final_matches = await self._apply_advanced_filtering(enhanced_matches, request)
            
            # Step 4: Store results in database
            await self._store_matching_results(session_id, request, final_matches)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Update session status
            await self.ai_service.update_session_status(
                session_id, ProcessingStatus.COMPLETED
            )
            
            return JobMatchResponse(
                resume_length=len(request.resume_text),
                total_matches=len(final_matches),
                matches=final_matches,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Job matching failed: {e}")
            if 'session_id' in locals():
                await self.ai_service.update_session_status(
                    session_id, ProcessingStatus.FAILED, str(e)
                )
            raise
    
    async def _perform_vector_search(self, request: JobMatchRequest, session_id: str) -> List[Dict]:
        """Perform vector similarity search using Pinecone"""
        try:
            # Use Pinecone for vector similarity search
            vector_matches = await pinecone_service.match_resume_to_jobs(
                resume_text=request.resume_text,
                job_ids=request.job_ids,
                top_k=min(request.top_k * 2, 50),  # Get more candidates for filtering
                min_similarity=0.6  # Lower threshold for initial search
            )
            
            logger.info(f"Vector search found {len(vector_matches)} initial matches")
            return vector_matches
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            # Fallback to basic semantic matching
            return await self._fallback_semantic_search(request.resume_text, request.job_ids)
    
    async def _enhance_with_semantic_analysis(self, 
                                            resume_text: str, 
                                            vector_matches: List[Dict],
                                            session_id: str) -> List[JobMatchResult]:
        """Enhance vector matches with detailed semantic analysis"""
        enhanced_matches = []
        
        for match in vector_matches[:self.config.max_results]:
            try:
                # Extract job metadata for analysis
                job_metadata = match.get('metadata', {})
                job_description = job_metadata.get('text_preview', '')
                
                if not job_description:
                    continue
                
                # Perform semantic analysis
                semantic_score = await self._calculate_semantic_score(
                    resume_text, job_description, session_id
                )
                
                # Calculate combined score
                vector_score = match.get('similarity_score', 0.0)
                combined_score = (
                    vector_score * self.config.vector_similarity_weight +
                    semantic_score * self.config.semantic_analysis_weight
                )
                
                # Create enhanced match result
                enhanced_match = JobMatchResult(
                    job_id=match['job_id'],
                    similarity_score=combined_score,
                    match_quality=self._calculate_match_quality(combined_score),
                    recommendation=self._generate_recommendation(combined_score, vector_score, semantic_score),
                    metadata={
                        **job_metadata,
                        'vector_score': vector_score,
                        'semantic_score': semantic_score,
                        'combined_score': combined_score
                    }
                )
                
                enhanced_matches.append(enhanced_match)
                
            except Exception as e:
                logger.warning(f"Failed to enhance match {match.get('job_id')}: {e}")
                continue
        
        # Sort by combined score
        enhanced_matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return enhanced_matches
    
    async def _calculate_semantic_score(self, resume_text: str, job_description: str, session_id: str) -> float:
        """Calculate semantic similarity score using AI analysis"""
        try:
            # Generate embeddings for both texts
            embeddings = await self.ai_service.get_embeddings(
                [resume_text, job_description], session_id
            )
            
            if len(embeddings) >= 2:
                # Calculate cosine similarity
                similarity = self.ai_service.calculate_semantic_similarity(
                    embeddings[0], embeddings[1]
                )
                return similarity
            
            # Fallback to basic text analysis
            return self._calculate_text_overlap(resume_text, job_description)
            
        except Exception as e:
            logger.error(f"Semantic score calculation failed: {e}")
            return 0.5  # Neutral score
    
    def _calculate_text_overlap(self, text1: str, text2: str) -> float:
        """Calculate basic text overlap as fallback"""
        try:
            # Simple word overlap calculation
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Text overlap calculation failed: {e}")
            return 0.0
    
    async def _apply_advanced_filtering(self, matches: List[JobMatchResult], request: JobMatchRequest) -> List[JobMatchResult]:
        """Apply advanced filtering and ranking to matches"""
        if not self.config.enable_advanced_filtering:
            return matches[:request.top_k]
        
        filtered_matches = []
        
        for match in matches:
            # Apply minimum score threshold
            if match.similarity_score < self.config.min_combined_score:
                continue
            
            # Apply user-specific filters if available
            if request.user_id:
                # Could add user preference filtering here
                pass
            
            # Apply job-specific filters
            metadata = match.metadata
            if metadata:
                # Filter by location if specified
                if 'location' in metadata and request.user_id:
                    # Could add location preference matching
                    pass
                
                # Filter by salary range if specified
                if 'salary_range' in metadata and request.user_id:
                    # Could add salary preference matching
                    pass
            
            filtered_matches.append(match)
        
        # Return top matches
        return filtered_matches[:request.top_k]
    
    async def _fallback_semantic_search(self, resume_text: str, job_ids: Optional[List[str]]) -> List[Dict]:
        """Fallback semantic search when Pinecone is unavailable"""
        try:
            # Use existing AI service for basic matching
            # This would need to be implemented based on available job data
            logger.info("Using fallback semantic search")
            return []
            
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return []
    
    async def _store_matching_results(self, session_id: str, request: JobMatchRequest, matches: List[JobMatchResult]):
        """Store matching results in database"""
        try:
            with get_db_context() as db:
                for match in matches:
                    analysis = JobMatchAnalysis(
                        session_id=session_id,
                        resume_text=request.resume_text[:1000],  # Store preview
                        job_id=match.job_id,
                        semantic_similarity=match.similarity_score,
                        match_quality=match.match_quality,
                        recommendation=match.recommendation,
                        metadata=match.metadata,
                        created_at=datetime.utcnow()
                    )
                    db.add(analysis)
                
                db.commit()
                logger.info(f"Stored {len(matches)} matching results")
                
        except Exception as e:
            logger.error(f"Failed to store matching results: {e}")
    
    def _calculate_match_quality(self, score: float) -> str:
        """Calculate match quality based on combined score"""
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.8:
            return "Very Good"
        elif score >= 0.7:
            return "Good"
        elif score >= 0.6:
            return "Fair"
        else:
            return "Poor"
    
    def _generate_recommendation(self, combined_score: float, vector_score: float, semantic_score: float) -> str:
        """Generate recommendation based on scores"""
        if combined_score >= 0.9:
            return "Strongly recommend - Excellent overall match"
        elif combined_score >= 0.8:
            if vector_score > semantic_score:
                return "Recommend - Strong vector similarity"
            else:
                return "Recommend - Strong semantic alignment"
        elif combined_score >= 0.7:
            return "Consider - Good potential match"
        elif combined_score >= 0.6:
            return "Review - Fair match, consider improvements"
        else:
            return "Not recommended - Poor match"
    
    async def batch_match_resumes(self, requests: List[JobMatchRequest]) -> List[JobMatchResponse]:
        """Batch process multiple resume-job matching requests"""
        results = []
        
        # Process in parallel with limited concurrency
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        
        async def process_request(request: JobMatchRequest) -> JobMatchResponse:
            async with semaphore:
                return await self.match_resume_to_jobs(request)
        
        # Create tasks for all requests
        tasks = [process_request(request) for request in requests]
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, JobMatchResponse):
                valid_results.append(result)
            else:
                logger.error(f"Batch processing failed: {result}")
        
        return valid_results
    
    async def get_matching_insights(self, resume_text: str, job_ids: List[str]) -> Dict[str, Any]:
        """Get detailed insights about matching patterns"""
        try:
            insights = {
                'skill_gaps': [],
                'strength_areas': [],
                'improvement_suggestions': [],
                'market_alignment': 0.0
            }
            
            # Analyze skill gaps
            if self.config.enable_skill_extraction:
                insights['skill_gaps'] = await self._analyze_skill_gaps(resume_text, job_ids)
            
            # Analyze strength areas
            insights['strength_areas'] = await self._analyze_strengths(resume_text, job_ids)
            
            # Generate improvement suggestions
            insights['improvement_suggestions'] = await self._generate_improvement_suggestions(
                resume_text, insights['skill_gaps']
            )
            
            # Calculate market alignment
            insights['market_alignment'] = await self._calculate_market_alignment(resume_text, job_ids)
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return insights
    
    async def _analyze_skill_gaps(self, resume_text: str, job_ids: List[str]) -> List[str]:
        """Analyze skill gaps between resume and job requirements"""
        try:
            # This would use AI to extract skills from resume and job descriptions
            # and identify gaps
            return ["Advanced Python", "Kubernetes", "Machine Learning"]
        except Exception as e:
            logger.error(f"Skill gap analysis failed: {e}")
            return []
    
    async def _analyze_strengths(self, resume_text: str, job_ids: List[str]) -> List[str]:
        """Analyze strength areas in the resume"""
        try:
            # This would identify strong areas in the resume
            return ["React Development", "API Design", "Team Leadership"]
        except Exception as e:
            logger.error(f"Strength analysis failed: {e}")
            return []
    
    async def _generate_improvement_suggestions(self, resume_text: str, skill_gaps: List[str]) -> List[str]:
        """Generate improvement suggestions based on skill gaps"""
        try:
            suggestions = []
            for skill in skill_gaps:
                suggestions.append(f"Consider adding {skill} to your skills section")
                suggestions.append(f"Highlight any {skill} experience in your work history")
            
            return suggestions[:5]  # Limit to top 5 suggestions
        except Exception as e:
            logger.error(f"Improvement suggestions failed: {e}")
            return []
    
    async def _calculate_market_alignment(self, resume_text: str, job_ids: List[str]) -> float:
        """Calculate overall market alignment score"""
        try:
            # This would analyze how well the resume aligns with current market demands
            return 0.75  # Placeholder score
        except Exception as e:
            logger.error(f"Market alignment calculation failed: {e}")
            return 0.5

# Global instance
enhanced_job_matcher = EnhancedJobMatcher()

