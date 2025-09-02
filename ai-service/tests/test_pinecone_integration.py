# ai-service/tests/test_pinecone_integration.py
"""
Comprehensive tests for Pinecone integration
Tests vector operations, semantic search, and job matching functionality
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from app.services.pinecone_service import (
    PineconeService, IndexType, VectorMetadata, SearchResult
)
from app.services.enhanced_job_matching import EnhancedJobMatcher, MatchingConfig
from app.models.schemas import (
    VectorSearchRequest, VectorUpsertRequest, JobMatchRequest,
    IndexType as SchemaIndexType
)

# Test data
SAMPLE_RESUME_TEXT = """
John Doe
Senior Software Engineer

EXPERIENCE:
- 5+ years of Python development
- React and Node.js expertise
- AWS cloud architecture
- Team leadership experience
- Built scalable microservices

SKILLS:
Python, React, Node.js, AWS, Docker, Kubernetes, SQL, Git

EDUCATION:
Computer Science BS, University of Technology
"""

SAMPLE_JOB_DESCRIPTION = """
Senior Python Developer

We are looking for a Senior Python Developer with 4+ years experience.
Requirements: Python, Django, React, AWS, microservices architecture.
You will lead a team and architect scalable solutions.

Skills needed:
- Python development
- React frontend
- AWS cloud services
- Microservices architecture
- Team leadership

Location: San Francisco, CA
Salary: $120k-150k
"""

@pytest.fixture
def pinecone_service():
    """Create Pinecone service instance for testing"""
    with patch.dict(os.environ, {
        'PINECONE_API_KEY': 'test-key',
        'PINECONE_ENVIRONMENT': 'us-west1-gcp',
        'OPENAI_API_KEY': 'test-openai-key'
    }):
        service = PineconeService()
        return service

@pytest.fixture
def enhanced_job_matcher():
    """Create enhanced job matcher instance for testing"""
    config = MatchingConfig(
        vector_similarity_weight=0.6,
        semantic_analysis_weight=0.4,
        min_combined_score=0.7,
        max_results=10
    )
    return EnhancedJobMatcher(config)

class TestPineconeService:
    """Test Pinecone service functionality"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, pinecone_service):
        """Test Pinecone service initialization"""
        assert pinecone_service.api_key == 'test-key'
        assert pinecone_service.environment == 'us-west1-gcp'
        assert pinecone_service.embedding_model == 'text-embedding-3-small'
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self, pinecone_service):
        """Test embedding generation"""
        with patch('app.services.pinecone_service.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3] * 512)]  # 1536 dimensions
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            embedding = await pinecone_service.generate_embedding("test text")
            
            assert embedding is not None
            assert len(embedding) == 1536
            assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_upsert_resume(self, pinecone_service):
        """Test resume upsert functionality"""
        with patch('app.services.pinecone_service.pinecone') as mock_pinecone:
            mock_index = Mock()
            mock_pinecone.Index.return_value = mock_index
            
            # Mock embedding generation
            with patch.object(pinecone_service, 'generate_embedding', return_value=[0.1] * 1536):
                success = await pinecone_service.upsert_resume(
                    resume_id="test_resume_1",
                    resume_text=SAMPLE_RESUME_TEXT,
                    user_id="user_123"
                )
                
                assert success is True
                mock_index.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upsert_job(self, pinecone_service):
        """Test job upsert functionality"""
        with patch('app.services.pinecone_service.pinecone') as mock_pinecone:
            mock_index = Mock()
            mock_pinecone.Index.return_value = mock_index
            
            # Mock embedding generation
            with patch.object(pinecone_service, 'generate_embedding', return_value=[0.1] * 1536):
                success = await pinecone_service.upsert_job(
                    job_id="test_job_1",
                    job_description=SAMPLE_JOB_DESCRIPTION
                )
                
                assert success is True
                mock_index.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_similar_resumes(self, pinecone_service):
        """Test resume similarity search"""
        with patch('app.services.pinecone_service.pinecone') as mock_pinecone:
            mock_index = Mock()
            mock_pinecone.Index.return_value = mock_index
            
            # Mock search results
            mock_match = Mock()
            mock_match.id = "resume_1"
            mock_match.score = 0.85
            mock_match.metadata = {
                'content_type': 'resume',
                'text_preview': 'Senior Software Engineer...'
            }
            
            mock_response = Mock()
            mock_response.matches = [mock_match]
            mock_index.query.return_value = mock_response
            
            # Mock embedding generation
            with patch.object(pinecone_service, 'generate_embedding', return_value=[0.1] * 1536):
                results = await pinecone_service.search_similar_resumes(
                    query_text="Python developer",
                    top_k=5
                )
                
                assert len(results) == 1
                assert results[0].content_id == "resume_1"
                assert results[0].similarity_score == 0.85
    
    @pytest.mark.asyncio
    async def test_search_similar_jobs(self, pinecone_service):
        """Test job similarity search"""
        with patch('app.services.pinecone_service.pinecone') as mock_pinecone:
            mock_index = Mock()
            mock_pinecone.Index.return_value = mock_index
            
            # Mock search results
            mock_match = Mock()
            mock_match.id = "job_1"
            mock_match.score = 0.92
            mock_match.metadata = {
                'content_type': 'job',
                'text_preview': 'Senior Python Developer...'
            }
            
            mock_response = Mock()
            mock_response.matches = [mock_match]
            mock_index.query.return_value = mock_response
            
            # Mock embedding generation
            with patch.object(pinecone_service, 'generate_embedding', return_value=[0.1] * 1536):
                results = await pinecone_service.search_similar_jobs(
                    query_text="Python developer",
                    top_k=5
                )
                
                assert len(results) == 1
                assert results[0].content_id == "job_1"
                assert results[0].similarity_score == 0.92
    
    @pytest.mark.asyncio
    async def test_match_resume_to_jobs(self, pinecone_service):
        """Test resume to jobs matching"""
        with patch('app.services.pinecone_service.pinecone') as mock_pinecone:
            mock_index = Mock()
            mock_pinecone.Index.return_value = mock_index
            
            # Mock search results
            mock_match = Mock()
            mock_match.id = "job_1"
            mock_match.score = 0.88
            mock_match.metadata = {
                'content_type': 'job',
                'text_preview': 'Senior Python Developer...'
            }
            
            mock_response = Mock()
            mock_response.matches = [mock_match]
            mock_index.query.return_value = mock_response
            
            # Mock embedding generation
            with patch.object(pinecone_service, 'generate_embedding', return_value=[0.1] * 1536):
                matches = await pinecone_service.match_resume_to_jobs(
                    resume_text=SAMPLE_RESUME_TEXT,
                    top_k=10,
                    min_similarity=0.7
                )
                
                assert len(matches) == 1
                assert matches[0]['job_id'] == "job_1"
                assert matches[0]['similarity_score'] == 0.88
                assert matches[0]['match_quality'] == "Very Good"
    
    @pytest.mark.asyncio
    async def test_batch_upsert_resumes(self, pinecone_service):
        """Test batch resume upsert"""
        resumes = [
            {
                'id': 'resume_1',
                'text': SAMPLE_RESUME_TEXT,
                'user_id': 'user_1',
                'metadata': {'experience_years': 5}
            },
            {
                'id': 'resume_2',
                'text': SAMPLE_RESUME_TEXT,
                'user_id': 'user_2',
                'metadata': {'experience_years': 3}
            }
        ]
        
        with patch.object(pinecone_service, 'upsert_resume', return_value=True):
            results = await pinecone_service.batch_upsert_resumes(resumes)
            
            assert len(results) == 2
            assert results['resume_1'] is True
            assert results['resume_2'] is True
    
    @pytest.mark.asyncio
    async def test_delete_vector(self, pinecone_service):
        """Test vector deletion"""
        with patch('app.services.pinecone_service.pinecone') as mock_pinecone:
            mock_index = Mock()
            mock_pinecone.Index.return_value = mock_index
            
            success = await pinecone_service.delete_vector(
                vector_id="test_vector",
                index_type=IndexType.RESUMES
            )
            
            assert success is True
            mock_index.delete.assert_called_once_with(ids=["test_vector"])
    
    @pytest.mark.asyncio
    async def test_get_index_stats(self, pinecone_service):
        """Test index statistics retrieval"""
        with patch('app.services.pinecone_service.pinecone') as mock_pinecone:
            mock_index = Mock()
            mock_pinecone.Index.return_value = mock_index
            
            # Mock stats
            mock_stats = Mock()
            mock_stats.total_vector_count = 1000
            mock_stats.dimension = 1536
            mock_stats.index_fullness = 0.15
            mock_stats.namespaces = {'default': 1000}
            mock_index.describe_index_stats.return_value = mock_stats
            
            stats = await pinecone_service.get_index_stats(IndexType.RESUMES)
            
            assert stats['total_vector_count'] == 1000
            assert stats['dimension'] == 1536
            assert stats['index_fullness'] == 0.15

class TestEnhancedJobMatcher:
    """Test enhanced job matching functionality"""
    
    @pytest.mark.asyncio
    async def test_match_resume_to_jobs(self, enhanced_job_matcher):
        """Test enhanced job matching"""
        request = JobMatchRequest(
            resume_text=SAMPLE_RESUME_TEXT,
            top_k=5,
            min_similarity=0.7,
            user_id="user_123"
        )
        
        with patch.object(enhanced_job_matcher.ai_service, 'create_processing_session', return_value="session_123"):
            with patch.object(enhanced_job_matcher.ai_service, 'update_session_status'):
                with patch.object(enhanced_job_matcher, '_perform_vector_search') as mock_vector_search:
                    mock_vector_search.return_value = [
                        {
                            'job_id': 'job_1',
                            'similarity_score': 0.88,
                            'metadata': {'text_preview': SAMPLE_JOB_DESCRIPTION}
                        }
                    ]
                    
                    with patch.object(enhanced_job_matcher, '_enhance_with_semantic_analysis') as mock_enhance:
                        mock_enhance.return_value = [
                            JobMatchResult(
                                job_id='job_1',
                                similarity_score=0.85,
                                match_quality='Very Good',
                                recommendation='Recommend - Very good match',
                                metadata={}
                            )
                        ]
                        
                        with patch.object(enhanced_job_matcher, '_store_matching_results'):
                            response = await enhanced_job_matcher.match_resume_to_jobs(request)
                            
                            assert response.resume_length == len(SAMPLE_RESUME_TEXT)
                            assert response.total_matches == 1
                            assert response.matches[0].job_id == 'job_1'
                            assert response.matches[0].similarity_score == 0.85
    
    @pytest.mark.asyncio
    async def test_calculate_semantic_score(self, enhanced_job_matcher):
        """Test semantic score calculation"""
        with patch.object(enhanced_job_matcher.ai_service, 'get_embeddings') as mock_embeddings:
            mock_embeddings.return_value = [[0.1] * 1536, [0.2] * 1536]
            
            with patch.object(enhanced_job_matcher.ai_service, 'calculate_semantic_similarity', return_value=0.75):
                score = await enhanced_job_matcher._calculate_semantic_score(
                    SAMPLE_RESUME_TEXT,
                    SAMPLE_JOB_DESCRIPTION,
                    "session_123"
                )
                
                assert score == 0.75
    
    @pytest.mark.asyncio
    async def test_calculate_text_overlap(self, enhanced_job_matcher):
        """Test text overlap calculation"""
        text1 = "Python developer with React experience"
        text2 = "Senior Python developer React Node.js"
        
        overlap = enhanced_job_matcher._calculate_text_overlap(text1, text2)
        
        assert overlap > 0.0
        assert overlap <= 1.0
    
    @pytest.mark.asyncio
    async def test_batch_match_resumes(self, enhanced_job_matcher):
        """Test batch resume matching"""
        requests = [
            JobMatchRequest(resume_text=SAMPLE_RESUME_TEXT, top_k=3),
            JobMatchRequest(resume_text=SAMPLE_RESUME_TEXT, top_k=3)
        ]
        
        with patch.object(enhanced_job_matcher, 'match_resume_to_jobs') as mock_match:
            mock_match.return_value = JobMatchResponse(
                resume_length=len(SAMPLE_RESUME_TEXT),
                total_matches=1,
                matches=[],
                processing_time_ms=100.0
            )
            
            results = await enhanced_job_matcher.batch_match_resumes(requests)
            
            assert len(results) == 2
            assert all(isinstance(r, JobMatchResponse) for r in results)
    
    @pytest.mark.asyncio
    async def test_get_matching_insights(self, enhanced_job_matcher):
        """Test matching insights generation"""
        insights = await enhanced_job_matcher.get_matching_insights(
            SAMPLE_RESUME_TEXT,
            ["job_1", "job_2"]
        )
        
        assert 'skill_gaps' in insights
        assert 'strength_areas' in insights
        assert 'improvement_suggestions' in insights
        assert 'market_alignment' in insights

class TestVectorMetadata:
    """Test VectorMetadata class"""
    
    def test_metadata_creation(self):
        """Test metadata object creation"""
        metadata = VectorMetadata(
            content_type="resume",
            content_id="resume_123",
            user_id="user_456",
            session_id="session_789",
            experience_years=5,
            skills=["Python", "React"]
        )
        
        assert metadata.content_type == "resume"
        assert metadata.content_id == "resume_123"
        assert metadata.user_id == "user_456"
        assert metadata.session_id == "session_789"
        assert metadata.additional_metadata['experience_years'] == 5
        assert metadata.additional_metadata['skills'] == ["Python", "React"]
    
    def test_metadata_to_dict(self):
        """Test metadata to dictionary conversion"""
        metadata = VectorMetadata(
            content_type="job",
            content_id="job_123",
            experience_years=3
        )
        
        metadata_dict = metadata.to_dict()
        
        assert metadata_dict['content_type'] == "job"
        assert metadata_dict['content_id'] == "job_123"
        assert metadata_dict['experience_years'] == 3
        assert 'timestamp' in metadata_dict
        assert 'user_id' not in metadata_dict  # Should not be included if None

class TestSearchResult:
    """Test SearchResult dataclass"""
    
    def test_search_result_creation(self):
        """Test search result object creation"""
        result = SearchResult(
            content_id="resume_123",
            content_type="resume",
            similarity_score=0.85,
            metadata={'user_id': 'user_456'},
            content_preview="Senior Software Engineer..."
        )
        
        assert result.content_id == "resume_123"
        assert result.content_type == "resume"
        assert result.similarity_score == 0.85
        assert result.metadata['user_id'] == 'user_456'
        assert result.content_preview == "Senior Software Engineer..."

@pytest.mark.asyncio
async def test_integration_workflow():
    """Test complete integration workflow"""
    # This would test the full workflow from resume upload to job matching
    # In a real test environment, this would use actual Pinecone and OpenAI APIs
    
    with patch('app.services.pinecone_service.pinecone'):
        with patch('app.services.pinecone_service.OpenAI'):
            service = PineconeService()
            
            # Test the complete workflow
            assert service.api_key == 'test-key'
            assert service.embedding_model == 'text-embedding-3-small'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

