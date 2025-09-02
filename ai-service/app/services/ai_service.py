# ai-service/app/services/ai_service.py - Enhanced AI Service
import openai
import os
import json
import asyncio
import hashlib
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ..models.ai_models import (
    AIProcessingSession, Embedding, ResumeOptimization, 
    JobMatchAnalysis, AIServiceConfig
)
from ..database import get_db_context
from ..models.schemas import (
    OperationType, ProcessingStatus, ConfidenceLevel, 
    EmbeddingModel, ChatModel
)
from .cache_service import cache_service

logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    def __init__(self, message: str, error_type: str = "UNKNOWN", details: Dict = None):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}

class EnhancedAIService:
    """Enhanced AI Service with comprehensive functionality"""
    
    def __init__(self):
        # Initialize OpenAI client lazily
        self.client = None
        self.embedding_model = "text-embedding-3-small"
        self.chat_model = "gpt-4o-mini"
        self.max_retries = 3
        
        # Load configuration from database
        self._load_config()
    
    def _load_config(self):
        """Load configuration from database"""
        try:
            with get_db_context() as db:
                configs = db.query(AIServiceConfig).filter(
                    AIServiceConfig.is_active == True
                ).all()
                
                for config in configs:
                    if config.config_key == "default_embedding_model":
                        self.embedding_model = config.config_value
                    elif config.config_key == "default_chat_model":
                        self.chat_model = config.config_value
                    elif config.config_key == "max_retries":
                        self.max_retries = int(config.config_value)
                        
        except Exception as e:
            logger.warning(f"Failed to load configuration from database: {e}")
    
    def _get_client(self):
        """Lazy initialization of OpenAI client"""
        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise AIServiceError(
                    "OpenAI API key not configured",
                    error_type="API_KEY_MISSING"
                )
            self.client = openai.OpenAI(api_key=api_key)
        return self.client
    
    async def create_processing_session(self, operation_type: OperationType, user_id: Optional[str] = None) -> str:
        """Create a new processing session"""
        session_id = f"{operation_type}_{int(time.time())}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        
        with get_db_context() as db:
            session = AIProcessingSession(
                session_id=session_id,
                user_id=user_id,
                operation_type=operation_type.value,
                status=ProcessingStatus.PROCESSING.value,
                created_at=datetime.utcnow()
            )
            db.add(session)
            db.commit()
        
        return session_id
    
    async def update_session_status(self, session_id: str, status: ProcessingStatus, error_message: Optional[str] = None):
        """Update processing session status"""
        with get_db_context() as db:
            session = db.query(AIProcessingSession).filter(
                AIProcessingSession.session_id == session_id
            ).first()
            
            if session:
                session.status = status.value
                if status == ProcessingStatus.COMPLETED:
                    session.completed_at = datetime.utcnow()
                if error_message:
                    session.error_message = error_message
                db.commit()
    
    async def get_embeddings(self, texts: List[str], session_id: Optional[str] = None) -> List[List[float]]:
        """Generate embeddings with Redis caching and database storage"""
        try:
            # Filter out empty strings and ensure minimum length
            valid_texts = [text.strip() for text in texts if text and text.strip() and len(text.strip()) > 3]
            
            if not valid_texts:
                logger.warning("No valid texts for embedding generation")
                return []
            
            embeddings = []
            texts_to_generate = []
            text_indices = []
            
            # Check cache for each text
            for i, text in enumerate(valid_texts):
                cached_embedding = await cache_service.get_cached_embedding(text, self.embedding_model)
                if cached_embedding:
                    embeddings.append(cached_embedding)
                    logger.debug(f"Cache hit for embedding {i}")
                else:
                    embeddings.append(None)  # Placeholder
                    texts_to_generate.append(text)
                    text_indices.append(i)
            
            # Generate embeddings for texts not in cache
            if texts_to_generate:
                logger.info(f"Generating {len(texts_to_generate)} new embeddings")
                client = self._get_client()
                response = client.embeddings.create(
                    model=self.embedding_model,
                    input=texts_to_generate
                )
                
                new_embeddings = [embedding.embedding for embedding in response.data]
                
                # Cache new embeddings and update result list
                for i, (text, embedding) in enumerate(zip(texts_to_generate, new_embeddings)):
                    await cache_service.cache_embedding(text, embedding, self.embedding_model)
                    embeddings[text_indices[i]] = embedding
            
            # Store embeddings in database if session_id provided
            if session_id:
                await self._store_embeddings(session_id, valid_texts, embeddings)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []
    
    async def _store_embeddings(self, session_id: str, texts: List[str], embeddings: List[List[float]]):
        """Store embeddings in database"""
        try:
            with get_db_context() as db:
                for text, embedding in zip(texts, embeddings):
                    text_hash = hashlib.sha256(text.encode()).hexdigest()
                    
                    embedding_record = Embedding(
                        session_id=session_id,
                        text_hash=text_hash,
                        text_type="general",
                        embedding_vector=embedding,
                        model_name=self.embedding_model,
                        dimensions=len(embedding),
                        text_preview=text[:500],
                        created_at=datetime.utcnow()
                    )
                    db.add(embedding_record)
                
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to store embeddings: {e}")
    
    def calculate_semantic_similarity(self, e1: List[float], e2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        if not e1 or not e2:
            return 0.0
        try:
            v1 = np.array(e1).reshape(1, -1)
            v2 = np.array(e2).reshape(1, -1)
            sim = float(cosine_similarity(v1, v2)[0][0])
            return max(0.0, min(1.0, sim))
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    async def _get_ai_response(self, prompt: str, max_tokens: int = 1500, temperature: float = 0.2) -> str:
        """Get response from OpenAI with Redis caching and retries"""
        # Check cache first
        cached_response = await cache_service.get_cached_openai_response(
            prompt, self.chat_model, temperature, max_tokens
        )
        if cached_response:
            logger.debug("Cache hit for OpenAI response")
            return cached_response
        
        # Generate new response if not in cache
        for attempt in range(self.max_retries + 1):
            try:
                client = self._get_client()
                response = client.chat.completions.create(
                    model=self.chat_model,
                    messages=[
                        {"role": "system", "content": "You are an expert AI assistant. Always return valid JSON responses as requested."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                response_text = response.choices[0].message.content.strip()
                
                # Clean JSON response
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                
                response_text = response_text.strip()
                
                # Cache the response
                await cache_service.cache_openai_response(
                    prompt, response_text, self.chat_model, temperature, max_tokens
                )
                
                return response_text
                
            except Exception as e:
                if attempt == self.max_retries:
                    raise e
                await asyncio.sleep(1)  # Brief delay before retry
        
        return "{}"
    
    async def analyze_job_match(self, resume_text: str, job_description: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Analyze job match with comprehensive scoring and Redis caching"""
        # Check cache first
        cached_result = await cache_service.get_cached_job_match_result(
            resume_text, job_description, user_id
        )
        if cached_result:
            logger.info("Cache hit for job match analysis")
            return cached_result
        
        session_id = await self.create_processing_session(OperationType.JOB_MATCH, user_id)
        
        try:
            # Generate embeddings for semantic analysis
            texts_to_embed = [
                resume_text[:8000],  # Truncate to avoid token limits
                job_description[:8000],
                f"Skills and experience from resume: {resume_text[:2000]}",
                f"Job requirements: {job_description[:2000]}"
            ]
            
            embeddings = await self.get_embeddings(texts_to_embed, session_id)
            
            # Calculate semantic similarity
            semantic_similarity = 0.5
            if len(embeddings) >= 2:
                semantic_similarity = self.calculate_semantic_similarity(embeddings[0], embeddings[1])
            
            # Perform AI analysis
            analysis_prompt = f"""
You are an expert HR analyst. Analyze the match between this resume and job description.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Provide a detailed analysis as JSON with this exact structure:
{{
    "overall_match": 0.0-1.0,
    "skills_match": 0.0-1.0,
    "experience_match": 0.0-1.0,
    "location_match": 0.0-1.0,
    "salary_expectation_match": 0.0-1.0,
    "detailed_analysis": {{
        "matching_skills": ["skill1", "skill2"],
        "missing_skills": ["skill1", "skill2"],
        "experience_alignment": "explanation",
        "location_analysis": "explanation",
        "salary_analysis": "explanation"
    }},
    "recommendation": "detailed recommendation text",
    "confidence_indicators": {{
        "analysis_depth": "high/medium/low",
        "data_completeness": "high/medium/low",
        "match_certainty": "high/medium/low"
    }}
}}

Base your analysis on actual content, not assumptions. Be specific and detailed.
"""
            
            ai_response = await self._get_ai_response(analysis_prompt, max_tokens=1500)
            analysis = json.loads(ai_response)
            
            # Combine semantic similarity with AI analysis
            final_scores = {
                "overall": round((analysis["overall_match"] + semantic_similarity) / 2, 3),
                "skills": round(analysis["skills_match"], 3),
                "experience": round(analysis["experience_match"], 3),
                "location": round(analysis.get("location_match", 0.8), 3),
                "salary": round(analysis.get("salary_expectation_match", 0.75), 3)
            }
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(analysis, semantic_similarity)
            confidence_level = self._get_confidence_level(confidence_score)
            
            # Store analysis in database
            await self._store_job_analysis(session_id, resume_text, job_description, final_scores, analysis, semantic_similarity, confidence_score)
            
            # Update session status
            await self.update_session_status(session_id, ProcessingStatus.COMPLETED)
            
            result = {
                "session_id": session_id,
                "match_scores": final_scores,
                "recommendation": analysis["recommendation"],
                "confidence_score": confidence_score,
                "confidence_level": confidence_level,
                "confidence_interval": f"±{max(5, 100 - confidence_score):.1f}%",
                "semantic_similarity": round(semantic_similarity, 3),
                "detailed_analysis": analysis.get("detailed_analysis", {}),
                "processing_metadata": {
                    "model_used": self.chat_model,
                    "embedding_model": self.embedding_model,
                    "processing_time": "completed"
                }
            }
            
            # Cache the result
            await cache_service.cache_job_match_result(resume_text, job_description, result, user_id)
            
            return result
            
        except Exception as e:
            await self.update_session_status(session_id, ProcessingStatus.FAILED, str(e))
            raise AIServiceError(f"Job match analysis failed: {str(e)}", "AI_ANALYSIS_FAILED")
    
    async def optimize_resume(self, resume_text: str, job_description: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Optimize resume for specific job with Redis caching"""
        # Check cache first
        cached_result = await cache_service.get_cached_optimization_result(
            resume_text, job_description, user_id
        )
        if cached_result:
            logger.info("Cache hit for resume optimization")
            return cached_result
        
        session_id = await self.create_processing_session(OperationType.RESUME_OPTIMIZATION, user_id)
        
        try:
            optimization_prompt = f"""
You are an expert resume optimization specialist. Optimize this resume for the specific job description.

ORIGINAL RESUME:
{resume_text}

TARGET JOB DESCRIPTION:
{job_description}

Provide optimization as JSON with this exact structure:
{{
    "optimized_resume": "complete optimized resume text",
    "improvements_made": ["specific improvement 1", "specific improvement 2"],
    "keywords_added": ["keyword1", "keyword2"],
    "sections_enhanced": ["section1", "section2"],
    "ats_score_improvement": "+X%",
    "match_score_prediction": 0.0-1.0,
    "optimization_summary": "detailed summary of changes made",
    "before_after_comparison": {{
        "original_length": number,
        "optimized_length": number,
        "keywords_before": number,
        "keywords_after": number,
        "major_changes": ["change1", "change2"]
    }}
}}

Requirements:
1. Actually modify the resume content - don't just return the original
2. Add relevant keywords from the job description
3. Enhance bullet points with quantifiable achievements
4. Improve formatting and structure
5. Ensure ATS compatibility
6. Make at least 5 substantive improvements

Be specific and make real improvements, not generic suggestions.
"""
            
            ai_response = await self._get_ai_response(optimization_prompt, max_tokens=2500)
            optimization = json.loads(ai_response)
            
            # Calculate confidence score
            confidence_score = self._calculate_optimization_confidence(optimization)
            confidence_level = self._get_confidence_level(confidence_score)
            
            # Store optimization in database
            await self._store_resume_optimization(session_id, resume_text, job_description, optimization, confidence_score)
            
            # Update session status
            await self.update_session_status(session_id, ProcessingStatus.COMPLETED)
            
            result = {
                "session_id": session_id,
                "optimized_resume": optimization["optimized_resume"],
                "improvements_made": optimization["improvements_made"],
                "keywords_added": optimization["keywords_added"],
                "ats_score_improvement": optimization["ats_score_improvement"],
                "match_score_prediction": optimization["match_score_prediction"],
                "optimization_summary": optimization["optimization_summary"],
                "confidence_score": confidence_score,
                "confidence_level": confidence_level,
                "processing_metadata": {
                    "model_used": self.chat_model,
                    "processing_time": "completed"
                }
            }
            
            # Cache the result
            await cache_service.cache_optimization_result(resume_text, job_description, result, user_id)
            
            return result
            
        except Exception as e:
            await self.update_session_status(session_id, ProcessingStatus.FAILED, str(e))
            raise AIServiceError(f"Resume optimization failed: {str(e)}", "AI_OPTIMIZATION_FAILED")
    
    def _calculate_confidence_score(self, analysis: Dict, semantic_similarity: float) -> float:
        """Calculate confidence score for job matching"""
        confidence_factors = []
        
        # Factor 1: Analysis completeness (0-30 points)
        required_fields = ["overall_match", "skills_match", "experience_match", "recommendation"]
        completeness_score = min(30, len([f for f in required_fields if f in analysis]) * 7.5)
        confidence_factors.append(completeness_score)
        
        # Factor 2: Semantic similarity quality (0-25 points)
        similarity_score = min(25, semantic_similarity * 25)
        confidence_factors.append(similarity_score)
        
        # Factor 3: Analysis depth (0-25 points)
        depth_indicators = analysis.get("confidence_indicators", {})
        depth_score = 0
        if depth_indicators.get("analysis_depth") == "high":
            depth_score = 25
        elif depth_indicators.get("analysis_depth") == "medium":
            depth_score = 20
        else:
            depth_score = 15
        confidence_factors.append(depth_score)
        
        # Factor 4: Data completeness (0-20 points)
        completeness_indicators = depth_indicators.get("data_completeness", "medium")
        if completeness_indicators == "high":
            data_score = 20
        elif completeness_indicators == "medium":
            data_score = 15
        else:
            data_score = 10
        confidence_factors.append(data_score)
        
        # Calculate final confidence score
        total_confidence = sum(confidence_factors)
        return min(95.0, max(60.0, total_confidence))
    
    def _calculate_optimization_confidence(self, optimization: Dict) -> float:
        """Calculate confidence score for resume optimization"""
        confidence_factors = []
        
        # Factor 1: Number of improvements made (0-30 points)
        improvements_count = len(optimization.get("improvements_made", []))
        improvements_score = min(30, improvements_count * 6)
        confidence_factors.append(improvements_score)
        
        # Factor 2: Keywords added (0-25 points)
        keywords_count = len(optimization.get("keywords_added", []))
        keywords_score = min(25, keywords_count * 5)
        confidence_factors.append(keywords_score)
        
        # Factor 3: ATS improvement percentage (0-25 points)
        ats_improvement = optimization.get("ats_score_improvement", "0%")
        try:
            ats_percentage = float(ats_improvement.replace("%", "").replace("+", ""))
            ats_score = min(25, ats_percentage)
        except:
            ats_score = 15
        confidence_factors.append(ats_score)
        
        # Factor 4: Content quality (0-20 points)
        optimized_resume = optimization.get("optimized_resume", "")
        if len(optimized_resume) > 100:
            content_score = 20
        elif len(optimized_resume) > 50:
            content_score = 15
        else:
            content_score = 10
        confidence_factors.append(content_score)
        
        # Calculate final confidence score
        total_confidence = sum(confidence_factors)
        return min(95.0, max(60.0, total_confidence))
    
    def _get_confidence_level(self, confidence_score: float) -> str:
        """Convert confidence score to descriptive level"""
        if confidence_score >= 90:
            return ConfidenceLevel.VERY_HIGH
        elif confidence_score >= 80:
            return ConfidenceLevel.HIGH
        elif confidence_score >= 70:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    async def _store_job_analysis(self, session_id: str, resume_text: str, job_description: str, 
                                scores: Dict, analysis: Dict, semantic_similarity: float, confidence_score: float):
        """Store job analysis in database"""
        try:
            with get_db_context() as db:
                resume_hash = hashlib.sha256(resume_text.encode()).hexdigest()
                job_hash = hashlib.sha256(job_description.encode()).hexdigest()
                
                analysis_record = JobMatchAnalysis(
                    session_id=session_id,
                    resume_hash=resume_hash,
                    resume_preview=resume_text[:1000],
                    job_description_hash=job_hash,
                    job_description_preview=job_description[:1000],
                    match_scores=scores,
                    recommendation=analysis.get("recommendation", ""),
                    detailed_analysis=analysis.get("detailed_analysis", {}),
                    semantic_similarity=semantic_similarity,
                    confidence_score=confidence_score,
                    confidence_level=self._get_confidence_level(confidence_score),
                    analysis_depth=analysis.get("confidence_indicators", {}).get("analysis_depth", "medium"),
                    model_used=self.chat_model,
                    created_at=datetime.utcnow()
                )
                db.add(analysis_record)
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to store job analysis: {e}")
    
    async def _store_resume_optimization(self, session_id: str, resume_text: str, job_description: str,
                                       optimization: Dict, confidence_score: float):
        """Store resume optimization in database"""
        try:
            with get_db_context() as db:
                resume_hash = hashlib.sha256(resume_text.encode()).hexdigest()
                job_hash = hashlib.sha256(job_description.encode()).hexdigest()
                
                optimization_record = ResumeOptimization(
                    session_id=session_id,
                    original_resume_hash=resume_hash,
                    original_resume_preview=resume_text[:1000],
                    job_description_hash=job_hash,
                    job_description_preview=job_description[:1000],
                    optimized_resume=optimization["optimized_resume"],
                    improvements_made=optimization["improvements_made"],
                    keywords_added=optimization["keywords_added"],
                    ats_score_improvement=optimization["ats_score_improvement"],
                    match_score_prediction=optimization["match_score_prediction"],
                    confidence_score=confidence_score,
                    confidence_level=self._get_confidence_level(confidence_score),
                    quality_validation_passed=True,
                    model_used=self.chat_model,
                    created_at=datetime.utcnow()
                )
                db.add(optimization_record)
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to store resume optimization: {e}")

# Global service instance
ai_service = EnhancedAIService()
