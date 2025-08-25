# backend/app/services/job_matching_service.py
"""
Enterprise-Grade Semantic Job Matching Engine
Implements RAFT-powered matching beyond keyword-based systems
"""

import asyncio
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
import openai
from sklearn.metrics.pairwise import cosine_similarity
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticJobMatcher:
    """
    Advanced job matching using semantic understanding and multi-dimensional scoring
    """
    
    def __init__(self, openai_api_key: str):
        self.client = openai.OpenAI(api_key=openai_api_key)
        
        # Initialize sentence transformer for semantic matching
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Sentence transformer model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load sentence transformer: {e}")
            self.embedding_model = None
            
        # Matching configuration
        self.similarity_threshold = 0.75
        self.weights = {
            'skills_alignment': 0.40,      # Technical and soft skills match
            'experience_relevance': 0.30,  # Years and type of experience
            'role_progression': 0.20,      # Career advancement fit
            'company_culture': 0.10        # Culture and values alignment
        }
        
    def extract_job_requirements(self, job_description: str) -> Dict[str, any]:
        """
        Extract structured requirements from job description using AI
        """
        
        extraction_prompt = f"""
        Extract the following information from this job description and return as JSON:
        
        Job Description:
        {job_description}
        
        Extract:
        1. required_skills: List of technical skills mentioned
        2. preferred_skills: List of nice-to-have skills
        3. experience_years: Required years of experience (number)
        4. education_level: Required education level
        5. role_level: seniority level (entry/mid/senior/executive)
        6. industry: Industry sector
        7. company_size: Company size indicator if mentioned
        8. work_style: Remote/hybrid/onsite preferences
        9. key_responsibilities: Top 5 main job responsibilities
        10. company_values: Any company culture/values mentioned
        
        Return only valid JSON format.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert job requirements analyst. Always return valid JSON."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            requirements = json.loads(response.choices[0].message.content)
            logger.info(f"Successfully extracted job requirements: {len(requirements)} fields")
            return requirements
            
        except Exception as e:
            logger.error(f"Failed to extract job requirements: {e}")
            return self._fallback_requirements_extraction(job_description)
            
    def _fallback_requirements_extraction(self, job_description: str) -> Dict[str, any]:
        """
        Fallback requirements extraction using pattern matching
        """
        requirements = {
            'required_skills': [],
            'preferred_skills': [],
            'experience_years': 0,
            'education_level': 'Bachelor',
            'role_level': 'mid',
            'industry': 'Technology',
            'company_size': 'Medium',
            'work_style': 'Hybrid',
            'key_responsibilities': [],
            'company_values': []
        }
        
        # Extract years of experience with regex
        years_pattern = r'(\d+)[\+\-\s]*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)'
        years_match = re.search(years_pattern, job_description.lower())
        if years_match:
            requirements['experience_years'] = int(years_match.group(1))
            
        # Extract common skills
        common_skills = [
            'python', 'javascript', 'react', 'node.js', 'aws', 'docker', 
            'kubernetes', 'sql', 'postgresql', 'mongodb', 'git', 'ci/cd',
            'machine learning', 'data analysis', 'project management'
        ]
        
        found_skills = []
        for skill in common_skills:
            if skill.lower() in job_description.lower():
                found_skills.append(skill)
                
        requirements['required_skills'] = found_skills[:8]  # Top 8 skills
        
        return requirements
        
    def analyze_user_profile(self, resume_content: str, user_preferences: Dict = None) -> Dict[str, any]:
        """
        Analyze user profile from resume content and preferences
        """
        
        analysis_prompt = f"""
        Analyze this resume and extract user profile information as JSON:
        
        Resume Content:
        {resume_content}
        
        Extract:
        1. current_skills: List of technical and professional skills
        2. experience_years: Total years of professional experience
        3. education_level: Highest education level
        4. current_role_level: Current seniority (entry/mid/senior/executive)
        5. industry_experience: Industries worked in
        6. leadership_experience: Any management/leadership roles (true/false)
        7. company_types: Types of companies worked for (startup/enterprise/etc)
        8. recent_achievements: Top 3 quantified achievements
        9. career_trajectory: Overall career progression trend
        10. specializations: Key areas of expertise
        
        Return only valid JSON format.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert resume analyst. Always return valid JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            profile = json.loads(response.choices[0].message.content)
            
            # Add user preferences if provided
            if user_preferences:
                profile.update(user_preferences)
                
            logger.info(f"Successfully analyzed user profile: {len(profile)} attributes")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to analyze user profile: {e}")
            return self._fallback_profile_analysis(resume_content, user_preferences)
            
    def _fallback_profile_analysis(self, resume_content: str, user_preferences: Dict = None) -> Dict[str, any]:
        """
        Fallback profile analysis using basic pattern matching
        """
        profile = {
            'current_skills': [],
            'experience_years': 3,
            'education_level': 'Bachelor',
            'current_role_level': 'mid',
            'industry_experience': ['Technology'],
            'leadership_experience': False,
            'company_types': ['Medium'],
            'recent_achievements': [],
            'career_trajectory': 'Growing',
            'specializations': []
        }
        
        # Basic skill extraction
        common_skills = [
            'python', 'javascript', 'react', 'node.js', 'aws', 'docker', 
            'sql', 'git', 'project management', 'leadership', 'analytics'
        ]
        
        found_skills = []
        for skill in common_skills:
            if skill.lower() in resume_content.lower():
                found_skills.append(skill)
                
        profile['current_skills'] = found_skills
        
        # Check for leadership indicators
        leadership_terms = ['manager', 'lead', 'director', 'vp', 'head of', 'team lead']
        for term in leadership_terms:
            if term.lower() in resume_content.lower():
                profile['leadership_experience'] = True
                break
                
        # Add user preferences if provided
        if user_preferences:
            profile.update(user_preferences)
            
        return profile
        
    def calculate_skills_alignment(self, user_skills: List[str], job_skills: List[str]) -> float:
        """
        Calculate semantic similarity between user skills and job requirements
        """
        if not user_skills or not job_skills:
            return 0.0
            
        try:
            # Convert skills to text for embedding
            user_skills_text = " ".join(user_skills).lower()
            job_skills_text = " ".join(job_skills).lower()
            
            if self.embedding_model:
                # Use sentence transformers for semantic similarity
                user_embedding = self.embedding_model.encode([user_skills_text])
                job_embedding = self.embedding_model.encode([job_skills_text])
                
                similarity = cosine_similarity(user_embedding, job_embedding)[0][0]
                return float(similarity)
            else:
                # Fallback to keyword overlap
                user_set = set(skill.lower().strip() for skill in user_skills)
                job_set = set(skill.lower().strip() for skill in job_skills)
                
                intersection = len(user_set.intersection(job_set))
                union = len(user_set.union(job_set))
                
                return intersection / union if union > 0 else 0.0
                
        except Exception as e:
            logger.error(f"Failed to calculate skills alignment: {e}")
            return 0.0
            
    def calculate_experience_relevance(self, user_profile: Dict, job_requirements: Dict) -> float:
        """
        Calculate experience relevance score
        """
        score = 0.0
        
        # Years of experience matching
        user_years = user_profile.get('experience_years', 0)
        required_years = job_requirements.get('experience_years', 0)
        
        if required_years > 0:
            if user_years >= required_years:
                score += 0.5  # Meets requirements
                if user_years <= required_years + 2:
                    score += 0.2  # Not overqualified
            else:
                # Partial credit for close matches
                ratio = user_years / required_years
                score += 0.3 * ratio
                
        # Industry experience matching
        user_industries = user_profile.get('industry_experience', [])
        job_industry = job_requirements.get('industry', '')
        
        if job_industry.lower() in [ind.lower() for ind in user_industries]:
            score += 0.3
            
        return min(score, 1.0)
        
    def calculate_role_progression_fit(self, user_profile: Dict, job_requirements: Dict) -> float:
        """
        Calculate if this role represents good career progression
        """
        user_level = user_profile.get('current_role_level', 'mid')
        job_level = job_requirements.get('role_level', 'mid')
        
        # Define role hierarchy
        role_hierarchy = {
            'entry': 1,
            'mid': 2, 
            'senior': 3,
            'executive': 4
        }
        
        user_rank = role_hierarchy.get(user_level, 2)
        job_rank = role_hierarchy.get(job_level, 2)
        
        # Good progression: same level or one level up
        if job_rank == user_rank:
            return 0.8  # Same level (lateral move)
        elif job_rank == user_rank + 1:
            return 1.0  # One level up (promotion)
        elif job_rank == user_rank - 1:
            return 0.4  # One level down (might be acceptable)
        elif job_rank > user_rank + 1:
            return 0.2  # Too senior (overreach)
        else:
            return 0.1  # Too junior (underutilizing skills)
            
    def calculate_company_culture_match(self, user_profile: Dict, job_requirements: Dict) -> float:
        """
        Calculate culture and values alignment
        """
        score = 0.5  # Base score
        
        # Company size preference
        user_company_types = user_profile.get('company_types', [])
        job_company_size = job_requirements.get('company_size', 'Medium')
        
        if job_company_size in user_company_types:
            score += 0.3
            
        # Work style preference
        user_work_style = user_profile.get('preferred_work_style', 'Hybrid')
        job_work_style = job_requirements.get('work_style', 'Hybrid')
        
        if user_work_style == job_work_style:
            score += 0.2
            
        return min(score, 1.0)
        
    def calculate_composite_match_score(self, user_profile: Dict, job_requirements: Dict) -> Dict[str, float]:
        """
        Calculate overall job match score using weighted components
        """
        # Calculate individual component scores
        skills_score = self.calculate_skills_alignment(
            user_profile.get('current_skills', []),
            job_requirements.get('required_skills', []) + job_requirements.get('preferred_skills', [])
        )
        
        experience_score = self.calculate_experience_relevance(user_profile, job_requirements)
        progression_score = self.calculate_role_progression_fit(user_profile, job_requirements)
        culture_score = self.calculate_company_culture_match(user_profile, job_requirements)
        
        # Calculate weighted composite score
        composite_score = (
            skills_score * self.weights['skills_alignment'] +
            experience_score * self.weights['experience_relevance'] +
            progression_score * self.weights['role_progression'] +
            culture_score * self.weights['company_culture']
        )
        
        return {
            'composite_score': round(composite_score, 3),
            'skills_alignment': round(skills_score, 3),
            'experience_relevance': round(experience_score, 3),
            'role_progression_fit': round(progression_score, 3),
            'company_culture_match': round(culture_score, 3),
            'confidence_level': 'High' if composite_score > 0.8 else 'Medium' if composite_score > 0.6 else 'Low'
        }
        
    async def match_jobs_for_user(self, resume_content: str, job_descriptions: List[Dict], 
                                 user_preferences: Dict = None, limit: int = 20) -> List[Dict]:
        """
        Main method to match jobs for a user
        """
        try:
            # Analyze user profile
            user_profile = self.analyze_user_profile(resume_content, user_preferences)
            
            # Match each job
            matched_jobs = []
            
            for job in job_descriptions:
                # Extract job requirements
                job_requirements = self.extract_job_requirements(job.get('description', ''))
                
                # Calculate match scores
                match_scores = self.calculate_composite_match_score(user_profile, job_requirements)
                
                # Create matched job object
                matched_job = {
                    'job_id': job.get('id', ''),
                    'title': job.get('title', ''),
                    'company': job.get('company', ''),
                    'location': job.get('location', ''),
                    'salary_range': job.get('salary_range', ''),
                    'job_type': job.get('job_type', 'Full-time'),
                    'remote_option': job.get('remote_option', False),
                    'posted_date': job.get('posted_date', datetime.now().isoformat()),
                    'description': job.get('description', ''),
                    'match_scores': match_scores,
                    'match_reasons': self.generate_match_reasons(user_profile, job_requirements, match_scores),
                    'missing_skills': self.identify_missing_skills(user_profile, job_requirements),
                    'application_url': job.get('application_url', ''),
                    'source': job.get('source', 'manual')
                }
                
                matched_jobs.append(matched_job)
                
            # Sort by composite score and return top matches
            matched_jobs.sort(key=lambda x: x['match_scores']['composite_score'], reverse=True)
            
            logger.info(f"Successfully matched {len(matched_jobs)} jobs, returning top {limit}")
            return matched_jobs[:limit]
            
        except Exception as e:
            logger.error(f"Failed to match jobs for user: {e}")
            return []
            
    def generate_match_reasons(self, user_profile: Dict, job_requirements: Dict, match_scores: Dict) -> List[str]:
        """
        Generate human-readable reasons for job match
        """
        reasons = []
        
        if match_scores['skills_alignment'] > 0.7:
            reasons.append(f"Strong skills match ({int(match_scores['skills_alignment'] * 100)}%)")
            
        if match_scores['experience_relevance'] > 0.7:
            years = user_profile.get('experience_years', 0)
            reasons.append(f"Experience aligns well ({years} years)")
            
        if match_scores['role_progression_fit'] > 0.8:
            reasons.append("Great career advancement opportunity")
            
        if match_scores['company_culture_match'] > 0.7:
            reasons.append("Company culture seems like a good fit")
            
        # Add specific skill matches
        user_skills = set(skill.lower() for skill in user_profile.get('current_skills', []))
        job_skills = set(skill.lower() for skill in job_requirements.get('required_skills', []))
        common_skills = user_skills.intersection(job_skills)
        
        if common_skills:
            top_skills = list(common_skills)[:3]
            reasons.append(f"Key skills match: {', '.join(top_skills)}")
            
        return reasons[:4]  # Return top 4 reasons
        
    def identify_missing_skills(self, user_profile: Dict, job_requirements: Dict) -> List[str]:
        """
        Identify skills gap for improvement recommendations
        """
        user_skills = set(skill.lower().strip() for skill in user_profile.get('current_skills', []))
        required_skills = set(skill.lower().strip() for skill in job_requirements.get('required_skills', []))
        
        missing_skills = required_skills - user_skills
        return list(missing_skills)[:5]  # Return top 5 missing skills


# Usage example and testing functions
async def test_job_matching():
    """
    Test function for the job matching service
    """
    import os
    
    # Initialize matcher
    matcher = SemanticJobMatcher(os.getenv("OPENAI_API_KEY"))
    
    # Sample resume content
    sample_resume = """
    John Doe
    Senior Software Engineer
    
    Experience:
    - 5 years of Python development
    - React and Node.js expertise  
    - AWS cloud architecture
    - Team leadership experience
    - Built scalable microservices
    
    Education: Computer Science BS
    """
    
    # Sample job descriptions
    sample_jobs = [
        {
            'id': 'job_1',
            'title': 'Senior Python Developer',
            'company': 'TechCorp',
            'location': 'San Francisco, CA',
            'salary_range': '$120k-150k',
            'description': '''
            We are looking for a Senior Python Developer with 4+ years experience.
            Requirements: Python, Django, React, AWS, microservices architecture.
            You will lead a team and architect scalable solutions.
            '''
        },
        {
            'id': 'job_2', 
            'title': 'Frontend React Developer',
            'company': 'StartupXYZ',
            'location': 'Remote',
            'salary_range': '$80k-100k',
            'description': '''
            Junior to Mid-level React developer needed.
            Requirements: React, JavaScript, CSS, 2+ years experience.
            Nice to have: Node.js, TypeScript.
            '''
        }
    ]
    
    # Test matching
    matches = await matcher.match_jobs_for_user(sample_resume, sample_jobs)
    
    # Print results
    print("\n🎯 Job Matching Results:")
    print("=" * 50)
    
    for match in matches:
        print(f"\n📋 {match['title']} at {match['company']}")
        print(f"📊 Match Score: {match['match_scores']['composite_score']:.2%}")
        print(f"✅ Reasons: {', '.join(match['match_reasons'])}")
        if match['missing_skills']:
            print(f"📈 Skills to develop: {', '.join(match['missing_skills'])}")
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(test_job_matching())