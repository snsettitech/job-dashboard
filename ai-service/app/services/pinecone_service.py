# ai-service/app/services/pinecone_service.py
"""
Pinecone Vector Database Service for Semantic Search and Job Matching
Provides high-performance vector similarity search for resumes and job descriptions
"""

import os
import json
import logging
import asyncio
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import uuid
import hashlib
import numpy as np
from dataclasses import dataclass
from enum import Enum

import pinecone
from openai import OpenAI

from ..models.ai_models import Embedding, AIProcessingSession
from ..database import get_db_context
from .cache_service import cache_service

logger = logging.getLogger(__name__)

class IndexType(Enum):
    """Pinecone index types for different use cases"""
    RESUMES = "resumes"
    JOBS = "jobs"
    SKILLS = "skills"
    COMPANIES = "companies"

class VectorMetadata:
    """Standardized metadata structure for Pinecone vectors"""
    
    def __init__(self, 
                 content_type: str,
                 content_id: str,
                 user_id: Optional[str] = None,
                 session_id: Optional[str] = None,
                 **kwargs):
        self.content_type = content_type  # resume, job, skill, company
        self.content_id = content_id
        self.user_id = user_id
        self.session_id = session_id
        self.timestamp = datetime.utcnow().isoformat()
        self.additional_metadata = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Pinecone storage"""
        metadata = {
            'content_type': self.content_type,
            'content_id': self.content_id,
            'timestamp': self.timestamp,
            **self.additional_metadata
        }
        
        if self.user_id:
            metadata['user_id'] = self.user_id
        if self.session_id:
            metadata['session_id'] = self.session_id
            
        return metadata

@dataclass
class SearchResult:
    """Structured search result"""
    content_id: str
    content_type: str
    similarity_score: float
    metadata: Dict[str, Any]
    content_preview: Optional[str] = None

class PineconeService:
    """
    Pinecone Vector Database Service for semantic search and job matching
    """
    
    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.environment = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
        self.openai_client = None
        self.embedding_model = "text-embedding-3-small"
        
        # Index configurations
        self.index_configs = {
            IndexType.RESUMES: {
                'name': 'resumes-index',
                'dimension': 1536,  # text-embedding-3-small dimension
                'metric': 'cosine',
                'pod_type': 'p1.x1'  # Production pod type
            },
            IndexType.JOBS: {
                'name': 'jobs-index', 
                'dimension': 1536,
                'metric': 'cosine',
                'pod_type': 'p1.x1'
            },
            IndexType.SKILLS: {
                'name': 'skills-index',
                'dimension': 1536,
                'metric': 'cosine',
                'pod_type': 'p1.x1'
            },
            IndexType.COMPANIES: {
                'name': 'companies-index',
                'dimension': 1536,
                'metric': 'cosine',
                'pod_type': 'p1.x1'
            }
        }
        
        # Initialize Pinecone
        self._initialize_pinecone()
        
    def _initialize_pinecone(self):
        """Initialize Pinecone client and create indexes if needed"""
        try:
            if not self.api_key:
                logger.warning("PINECONE_API_KEY not found. Pinecone service will be disabled.")
                return
                
            pinecone.init(api_key=self.api_key, environment=self.environment)
            logger.info(f"Pinecone initialized in environment: {self.environment}")
            
            # Create indexes if they don't exist
            self._ensure_indexes_exist()
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise
    
    def _ensure_indexes_exist(self):
        """Create Pinecone indexes if they don't exist"""
        try:
            existing_indexes = pinecone.list_indexes()
            
            for index_type, config in self.index_configs.items():
                index_name = config['name']
                
                if index_name not in existing_indexes:
                    logger.info(f"Creating Pinecone index: {index_name}")
                    pinecone.create_index(
                        name=index_name,
                        dimension=config['dimension'],
                        metric=config['metric'],
                        pod_type=config['pod_type']
                    )
                    logger.info(f"Successfully created index: {index_name}")
                else:
                    logger.info(f"Index already exists: {index_name}")
                    
        except Exception as e:
            logger.error(f"Failed to ensure indexes exist: {e}")
            raise
    
    def _get_openai_client(self):
        """Lazy initialization of OpenAI client"""
        if self.openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            self.openai_client = OpenAI(api_key=api_key)
        return self.openai_client
    
    async def generate_embedding(self, text: str, use_cache: bool = True) -> Optional[List[float]]:
        """Generate embedding for text with optional caching"""
        try:
            # Check cache first
            if use_cache:
                cached_embedding = await cache_service.get_cached_embedding(text, self.embedding_model)
                if cached_embedding:
                    logger.debug(f"Cache hit for embedding: {text[:50]}...")
                    return cached_embedding
            
            # Generate new embedding
            client = self._get_openai_client()
            response = client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            
            embedding = response.data[0].embedding
            
            # Cache the embedding
            if use_cache:
                await cache_service.cache_embedding(text, self.embedding_model, embedding)
            
            logger.debug(f"Generated embedding for: {text[:50]}...")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    async def upsert_resume(self, 
                           resume_id: str,
                           resume_text: str,
                           user_id: Optional[str] = None,
                           session_id: Optional[str] = None,
                           metadata: Optional[Dict] = None) -> bool:
        """Upsert resume embedding to Pinecone"""
        try:
            # Generate embedding
            embedding = await self.generate_embedding(resume_text)
            if not embedding:
                return False
            
            # Create metadata
            vector_metadata = VectorMetadata(
                content_type="resume",
                content_id=resume_id,
                user_id=user_id,
                session_id=session_id,
                text_length=len(resume_text),
                text_preview=resume_text[:500],
                **(metadata or {})
            )
            
            # Upsert to Pinecone
            index = pinecone.Index(self.index_configs[IndexType.RESUMES]['name'])
            index.upsert(
                vectors=[{
                    'id': resume_id,
                    'values': embedding,
                    'metadata': vector_metadata.to_dict()
                }]
            )
            
            # Store in local database for backup
            await self._store_embedding_locally(
                session_id=session_id,
                content_id=resume_id,
                content_type="resume",
                embedding=embedding,
                text_preview=resume_text[:500]
            )
            
            logger.info(f"Successfully upserted resume: {resume_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert resume {resume_id}: {e}")
            return False
    
    async def upsert_job(self,
                        job_id: str,
                        job_description: str,
                        job_metadata: Optional[Dict] = None,
                        session_id: Optional[str] = None) -> bool:
        """Upsert job description embedding to Pinecone"""
        try:
            # Generate embedding
            embedding = await self.generate_embedding(job_description)
            if not embedding:
                return False
            
            # Create metadata
            vector_metadata = VectorMetadata(
                content_type="job",
                content_id=job_id,
                session_id=session_id,
                text_length=len(job_description),
                text_preview=job_description[:500],
                **(job_metadata or {})
            )
            
            # Upsert to Pinecone
            index = pinecone.Index(self.index_configs[IndexType.JOBS]['name'])
            index.upsert(
                vectors=[{
                    'id': job_id,
                    'values': embedding,
                    'metadata': vector_metadata.to_dict()
                }]
            )
            
            # Store in local database for backup
            await self._store_embedding_locally(
                session_id=session_id,
                content_id=job_id,
                content_type="job",
                embedding=embedding,
                text_preview=job_description[:500]
            )
            
            logger.info(f"Successfully upserted job: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert job {job_id}: {e}")
            return False
    
    async def search_similar_resumes(self,
                                   query_text: str,
                                   top_k: int = 10,
                                   filter_metadata: Optional[Dict] = None) -> List[SearchResult]:
        """Search for similar resumes using semantic similarity"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query_text)
            if not query_embedding:
                return []
            
            # Search in Pinecone
            index = pinecone.Index(self.index_configs[IndexType.RESUMES]['name'])
            
            search_kwargs = {
                'vector': query_embedding,
                'top_k': top_k,
                'include_metadata': True
            }
            
            if filter_metadata:
                search_kwargs['filter'] = filter_metadata
            
            results = index.query(**search_kwargs)
            
            # Convert to SearchResult objects
            search_results = []
            for match in results.matches:
                search_result = SearchResult(
                    content_id=match.id,
                    content_type=match.metadata.get('content_type', 'resume'),
                    similarity_score=match.score,
                    metadata=match.metadata,
                    content_preview=match.metadata.get('text_preview')
                )
                search_results.append(search_result)
            
            logger.info(f"Found {len(search_results)} similar resumes")
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search similar resumes: {e}")
            return []
    
    async def search_similar_jobs(self,
                                query_text: str,
                                top_k: int = 10,
                                filter_metadata: Optional[Dict] = None) -> List[SearchResult]:
        """Search for similar job descriptions using semantic similarity"""
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query_text)
            if not query_embedding:
                return []
            
            # Search in Pinecone
            index = pinecone.Index(self.index_configs[IndexType.JOBS]['name'])
            
            search_kwargs = {
                'vector': query_embedding,
                'top_k': top_k,
                'include_metadata': True
            }
            
            if filter_metadata:
                search_kwargs['filter'] = filter_metadata
            
            results = index.query(**search_kwargs)
            
            # Convert to SearchResult objects
            search_results = []
            for match in results.matches:
                search_result = SearchResult(
                    content_id=match.id,
                    content_type=match.metadata.get('content_type', 'job'),
                    similarity_score=match.score,
                    metadata=match.metadata,
                    content_preview=match.metadata.get('text_preview')
                )
                search_results.append(search_result)
            
            logger.info(f"Found {len(search_results)} similar jobs")
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search similar jobs: {e}")
            return []
    
    async def match_resume_to_jobs(self,
                                 resume_text: str,
                                 job_ids: Optional[List[str]] = None,
                                 top_k: int = 20,
                                 min_similarity: float = 0.7) -> List[Dict]:
        """Match resume to jobs using semantic similarity"""
        try:
            # Generate resume embedding
            resume_embedding = await self.generate_embedding(resume_text)
            if not resume_embedding:
                return []
            
            # Search for similar jobs
            index = pinecone.Index(self.index_configs[IndexType.JOBS]['name'])
            
            search_kwargs = {
                'vector': resume_embedding,
                'top_k': top_k,
                'include_metadata': True
            }
            
            if job_ids:
                search_kwargs['filter'] = {'content_id': {'$in': job_ids}}
            
            results = index.query(**search_kwargs)
            
            # Process and filter results
            matches = []
            for match in results.matches:
                if match.score >= min_similarity:
                    match_data = {
                        'job_id': match.id,
                        'similarity_score': match.score,
                        'metadata': match.metadata,
                        'match_quality': self._calculate_match_quality(match.score),
                        'recommendation': self._generate_match_recommendation(match.score)
                    }
                    matches.append(match_data)
            
            # Sort by similarity score
            matches.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            logger.info(f"Found {len(matches)} job matches for resume")
            return matches
            
        except Exception as e:
            logger.error(f"Failed to match resume to jobs: {e}")
            return []
    
    async def match_jobs_to_resume(self,
                                 job_description: str,
                                 resume_ids: Optional[List[str]] = None,
                                 top_k: int = 20,
                                 min_similarity: float = 0.7) -> List[Dict]:
        """Match job to resumes using semantic similarity"""
        try:
            # Generate job embedding
            job_embedding = await self.generate_embedding(job_description)
            if not job_embedding:
                return []
            
            # Search for similar resumes
            index = pinecone.Index(self.index_configs[IndexType.RESUMES]['name'])
            
            search_kwargs = {
                'vector': job_embedding,
                'top_k': top_k,
                'include_metadata': True
            }
            
            if resume_ids:
                search_kwargs['filter'] = {'content_id': {'$in': resume_ids}}
            
            results = index.query(**search_kwargs)
            
            # Process and filter results
            matches = []
            for match in results.matches:
                if match.score >= min_similarity:
                    match_data = {
                        'resume_id': match.id,
                        'similarity_score': match.score,
                        'metadata': match.metadata,
                        'match_quality': self._calculate_match_quality(match.score),
                        'recommendation': self._generate_match_recommendation(match.score)
                    }
                    matches.append(match_data)
            
            # Sort by similarity score
            matches.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            logger.info(f"Found {len(matches)} resume matches for job")
            return matches
            
        except Exception as e:
            logger.error(f"Failed to match job to resumes: {e}")
            return []
    
    async def batch_upsert_resumes(self, resumes: List[Dict]) -> Dict[str, bool]:
        """Batch upsert multiple resumes"""
        results = {}
        
        for resume in resumes:
            resume_id = resume.get('id')
            resume_text = resume.get('text', '')
            user_id = resume.get('user_id')
            metadata = resume.get('metadata', {})
            
            if resume_id and resume_text:
                success = await self.upsert_resume(
                    resume_id=resume_id,
                    resume_text=resume_text,
                    user_id=user_id,
                    metadata=metadata
                )
                results[resume_id] = success
            else:
                results[resume_id or 'unknown'] = False
        
        return results
    
    async def batch_upsert_jobs(self, jobs: List[Dict]) -> Dict[str, bool]:
        """Batch upsert multiple jobs"""
        results = {}
        
        for job in jobs:
            job_id = job.get('id')
            job_description = job.get('description', '')
            metadata = job.get('metadata', {})
            
            if job_id and job_description:
                success = await self.upsert_job(
                    job_id=job_id,
                    job_description=job_description,
                    job_metadata=metadata
                )
                results[job_id] = success
            else:
                results[job_id or 'unknown'] = False
        
        return results
    
    async def delete_vector(self, vector_id: str, index_type: IndexType) -> bool:
        """Delete a vector from Pinecone"""
        try:
            index_name = self.index_configs[index_type]['name']
            index = pinecone.Index(index_name)
            index.delete(ids=[vector_id])
            
            logger.info(f"Successfully deleted vector: {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vector {vector_id}: {e}")
            return False
    
    async def get_index_stats(self, index_type: IndexType) -> Dict:
        """Get statistics for a Pinecone index"""
        try:
            index_name = self.index_configs[index_type]['name']
            index = pinecone.Index(index_name)
            stats = index.describe_index_stats()
            
            return {
                'index_name': index_name,
                'total_vector_count': stats.total_vector_count,
                'dimension': stats.dimension,
                'index_fullness': stats.index_fullness,
                'namespaces': stats.namespaces
            }
            
        except Exception as e:
            logger.error(f"Failed to get index stats for {index_type}: {e}")
            return {}
    
    def _calculate_match_quality(self, similarity_score: float) -> str:
        """Calculate match quality based on similarity score"""
        if similarity_score >= 0.9:
            return "Excellent"
        elif similarity_score >= 0.8:
            return "Very Good"
        elif similarity_score >= 0.7:
            return "Good"
        elif similarity_score >= 0.6:
            return "Fair"
        else:
            return "Poor"
    
    def _generate_match_recommendation(self, similarity_score: float) -> str:
        """Generate recommendation based on similarity score"""
        if similarity_score >= 0.9:
            return "Strongly recommend - Excellent match"
        elif similarity_score >= 0.8:
            return "Recommend - Very good match"
        elif similarity_score >= 0.7:
            return "Consider - Good match"
        elif similarity_score >= 0.6:
            return "Review - Fair match"
        else:
            return "Not recommended - Poor match"
    
    async def _store_embedding_locally(self,
                                     session_id: Optional[str],
                                     content_id: str,
                                     content_type: str,
                                     embedding: List[float],
                                     text_preview: str) -> None:
        """Store embedding in local database as backup"""
        try:
            with get_db_context() as db:
                text_hash = hashlib.sha256(text_preview.encode()).hexdigest()
                
                embedding_record = Embedding(
                    session_id=session_id,
                    text_hash=text_hash,
                    text_type=content_type,
                    embedding_vector=embedding,
                    model_name=self.embedding_model,
                    dimensions=len(embedding),
                    text_preview=text_preview,
                    created_at=datetime.utcnow()
                )
                db.add(embedding_record)
                db.commit()
                
        except Exception as e:
            logger.warning(f"Failed to store embedding locally: {e}")

# Global instance
pinecone_service = PineconeService()

