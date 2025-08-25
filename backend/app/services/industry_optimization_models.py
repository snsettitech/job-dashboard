# backend/app/services/industry_optimization_models.py
"""
Industry-Specific Resume Optimization Models
Tailored optimization for different industries with specific keywords, metrics, and language patterns
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import openai
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OptimizationResult:
    """Result of industry-specific optimization"""
    industry: str
    optimized_content: str
    improvements_made: List[str]
    keyword_score_before: float
    keyword_score_after: float
    language_enhancement_score: float
    industry_alignment_score: float
    recommendations: List[str]

class IndustryOptimizer(ABC):
    """Base class for industry-specific optimizers"""
    
    def __init__(self, industry_name: str):
        self.industry_name = industry_name
        self.priority_keywords = []
        self.language_patterns = {}
        self.metric_types = []
        self.achievement_formats = []
        
    @abstractmethod
    def optimize_for_industry(self, resume_content: str, job_requirements: Dict = None) -> OptimizationResult:
        """Optimize resume for specific industry"""
        pass
    
    def extract_quantified_achievements(self, text: str) -> List[str]:
        """Extract achievements that contain numbers/metrics"""
        achievements = []
        
        # Patterns for quantified achievements
        patterns = [
            r'(increased|improved|reduced|grew|generated|saved|led|managed)\s+[^.]*?\d+[%$]?[^.]*',
            r'\d+[%$]?\s+(increase|improvement|reduction|growth|savings)',
            r'(team of|budget of|portfolio of)\s+\$?\d+[kmb]?',
            r'\d+\+?\s+(users|customers|clients|employees|projects)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            achievements.extend(matches)
            
        return achievements
    
    def calculate_keyword_density(self, text: str, keywords: List[str]) -> float:
        """Calculate keyword density for industry-specific terms"""
        text_lower = text.lower()
        total_keywords = len(keywords)
        found_keywords = 0
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found_keywords += 1
                
        return (found_keywords / total_keywords) * 100 if total_keywords > 0 else 0

class TechIndustryOptimizer(IndustryOptimizer):
    """Technology industry resume optimization"""
    
    def __init__(self):
        super().__init__("Technology")
        
        # Tech-specific keywords and terms
        self.priority_keywords = [
            # Programming Languages
            'python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c++',
            # Frameworks & Libraries  
            'react', 'angular', 'vue', 'django', 'flask', 'spring', 'express',
            # Cloud & DevOps
            'aws', 'gcp', 'azure', 'docker', 'kubernetes', 'terraform', 'jenkins',
            # Databases
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
            # Methodologies
            'agile', 'scrum', 'ci/cd', 'tdd', 'microservices', 'api design',
            # Concepts
            'scalability', 'performance', 'optimization', 'distributed systems',
            'machine learning', 'data pipeline', 'real-time', 'high availability'
        ]
        
        # Tech industry language patterns
        self.language_patterns = {
            'weak_to_strong': {
                'worked on': 'architected and developed',
                'helped with': 'led the development of',
                'was part of': 'contributed to',
                'used': 'leveraged',
                'made': 'engineered',
                'did': 'implemented',
                'fixed bugs': 'optimized system performance',
                'wrote code': 'developed scalable solutions'
            },
            'impact_verbs': [
                'architected', 'engineered', 'optimized', 'scaled', 'automated',
                'implemented', 'designed', 'built', 'developed', 'deployed',
                'integrated', 'migrated', 'refactored', 'enhanced'
            ]
        }
        
        # Tech metrics that matter
        self.metric_types = [
            'performance improvement (%)',
            'system uptime (%)',
            'user growth',
            'data volume processed',
            'response time reduction',
            'cost savings',
            'team size led',
            'code coverage (%)',
            'deployment frequency',
            'bug reduction (%)'
        ]
        
        # Achievement format templates
        self.achievement_formats = [
            "Architected {system} that {action} {metric}, resulting in {impact}",
            "Optimized {component} performance by {percentage}%, reducing {metric} from {before} to {after}",
            "Led development of {feature} serving {number}+ {users/requests/transactions} with {reliability}% uptime",
            "Implemented {technology} infrastructure that scaled to support {growth}% increase in {metric}"
        ]
    
    def optimize_for_industry(self, resume_content: str, job_requirements: Dict = None) -> OptimizationResult:
        """Optimize resume for tech industry"""
        
        # Calculate baseline scores
        keyword_score_before = self.calculate_keyword_density(resume_content, self.priority_keywords)
        
        improvements_made = []
        optimized_content = resume_content
        
        # 1. Enhance technical language
        optimized_content, language_improvements = self._enhance_technical_language(optimized_content)
        improvements_made.extend(language_improvements)
        
        # 2. Quantify technical achievements
        optimized_content, metric_improvements = self._quantify_technical_achievements(optimized_content)
        improvements_made.extend(metric_improvements)
        
        # 3. Inject relevant keywords
        optimized_content, keyword_improvements = self._inject_tech_keywords(optimized_content, job_requirements)
        improvements_made.extend(keyword_improvements)
        
        # 4. Optimize for technical leadership
        optimized_content, leadership_improvements = self._enhance_technical_leadership(optimized_content)
        improvements_made.extend(leadership_improvements)
        
        # Calculate post-optimization scores
        keyword_score_after = self.calculate_keyword_density(optimized_content, self.priority_keywords)
        
        # Generate recommendations
        recommendations = self._generate_tech_recommendations(optimized_content, job_requirements)
        
        return OptimizationResult(
            industry="Technology",
            optimized_content=optimized_content,
            improvements_made=improvements_made,
            keyword_score_before=keyword_score_before,
            keyword_score_after=keyword_score_after,
            language_enhancement_score=self._calculate_language_score(optimized_content),
            industry_alignment_score=self._calculate_tech_alignment_score(optimized_content),
            recommendations=recommendations
        )
    
    def _enhance_technical_language(self, content: str) -> Tuple[str, List[str]]:
        """Replace weak language with strong technical terms"""
        improvements = []
        enhanced_content = content
        
        for weak, strong in self.language_patterns['weak_to_strong'].items():
            if weak in content.lower():
                enhanced_content = re.sub(
                    r'\b' + re.escape(weak) + r'\b', 
                    strong, 
                    enhanced_content, 
                    flags=re.IGNORECASE
                )
                improvements.append(f"Enhanced language: '{weak}' → '{strong}'")
        
        return enhanced_content, improvements
    
    def _quantify_technical_achievements(self, content: str) -> Tuple[str, List[str]]:
        """Add quantified metrics to technical achievements"""
        improvements = []
        enhanced_content = content
        
        # Look for vague achievements and suggest quantification
        vague_patterns = [
            (r'improved performance', 'improved performance by 40%'),
            (r'reduced load time', 'reduced load time from 3s to 1.2s (60% improvement)'),
            (r'increased efficiency', 'increased system efficiency by 35%'),
            (r'optimized database', 'optimized database queries, reducing response time by 50%'),
            (r'scaled system', 'scaled system to handle 10x traffic increase'),
            (r'led team', 'led cross-functional team of 8 engineers')
        ]
        
        for pattern, replacement in vague_patterns:
            if re.search(pattern, enhanced_content, re.IGNORECASE):
                enhanced_content = re.sub(
                    pattern, replacement, enhanced_content, 
                    count=1, flags=re.IGNORECASE
                )
                improvements.append(f"Quantified achievement: added specific metrics")
        
        return enhanced_content, improvements
    
    def _inject_tech_keywords(self, content: str, job_requirements: Dict = None) -> Tuple[str, List[str]]:
        """Strategically inject relevant technical keywords"""
        improvements = []
        enhanced_content = content
        
        # Get keywords from job requirements if available
        target_keywords = []
        if job_requirements:
            target_keywords.extend(job_requirements.get('required_skills', []))
            target_keywords.extend(job_requirements.get('preferred_skills', []))
        
        # Add general high-value tech keywords
        target_keywords.extend(['microservices', 'scalability', 'cloud architecture', 'ci/cd', 'agile'])
        
        # Inject keywords naturally
        content_lower = enhanced_content.lower()
        for keyword in target_keywords[:5]:  # Top 5 keywords
            if keyword.lower() not in content_lower:
                # Find appropriate place to inject keyword
                if 'python' in keyword.lower() and 'python' not in content_lower:
                    enhanced_content = enhanced_content.replace(
                        'developed', f'developed Python-based', 1
                    )
                    improvements.append(f"Added keyword: {keyword}")
                elif 'aws' in keyword.lower() and 'aws' not in content_lower:
                    enhanced_content = enhanced_content.replace(
                        'cloud', 'AWS cloud', 1
                    )
                    improvements.append(f"Added keyword: {keyword}")
        
        return enhanced_content, improvements
    
    def _enhance_technical_leadership(self, content: str) -> Tuple[str, List[str]]:
        """Enhance technical leadership language"""
        improvements = []
        enhanced_content = content
        
        # Technical leadership patterns
        leadership_enhancements = [
            (r'managed team', 'led cross-functional engineering team'),
            (r'worked with team', 'collaborated with engineering teams'),
            (r'mentored', 'mentored junior developers and conducted code reviews'),
            (r'code review', 'conducted thorough code reviews and established best practices')
        ]
        
        for pattern, replacement in leadership_enhancements:
            if re.search(pattern, enhanced_content, re.IGNORECASE):
                enhanced_content = re.sub(
                    pattern, replacement, enhanced_content,
                    count=1, flags=re.IGNORECASE
                )
                improvements.append(f"Enhanced technical leadership language")
        
        return enhanced_content, improvements
    
    def _calculate_language_score(self, content: str) -> float:
        """Calculate technical language strength score"""
        strong_verbs = self.language_patterns['impact_verbs']
        content_lower = content.lower()
        
        found_verbs = sum(1 for verb in strong_verbs if verb in content_lower)
        return min(100, (found_verbs / len(strong_verbs)) * 100)
    
    def _calculate_tech_alignment_score(self, content: str) -> float:
        """Calculate overall tech industry alignment"""
        score = 0
        content_lower = content.lower()
        
        # Technical depth indicators
        tech_depth_terms = ['architecture', 'scalable', 'performance', 'optimization', 'distributed']
        score += sum(5 for term in tech_depth_terms if term in content_lower)
        
        # Modern tech stack
        modern_stack = ['microservices', 'docker', 'kubernetes', 'ci/cd', 'cloud']
        score += sum(10 for term in modern_stack if term in content_lower)
        
        # Quantified achievements
        numbers = len(re.findall(r'\d+[%$]?', content))
        score += min(numbers * 3, 30)  # Up to 30 points for metrics
        
        return min(100, score)
    
    def _generate_tech_recommendations(self, content: str, job_requirements: Dict = None) -> List[str]:
        """Generate tech industry specific recommendations"""
        recommendations = []
        content_lower = content.lower()
        
        # Check for missing critical elements
        if 'github' not in content_lower and 'portfolio' not in content_lower:
            recommendations.append("Include GitHub profile or portfolio link to showcase code")
        
        if len(re.findall(r'\d+[%$]?', content)) < 3:
            recommendations.append("Add more quantified technical achievements (performance improvements, user growth, etc.)")
        
        if not any(term in content_lower for term in ['microservices', 'scalable', 'distributed']):
            recommendations.append("Highlight experience with scalable systems and modern architectures")
        
        if not any(term in content_lower for term in ['team', 'led', 'mentored']):
            recommendations.append("Emphasize technical leadership and team collaboration experience")
        
        if not any(term in content_lower for term in ['ci/cd', 'devops', 'automation']):
            recommendations.append("Include DevOps and automation experience if applicable")
        
        return recommendations

class FinanceIndustryOptimizer(IndustryOptimizer):
    """Finance industry resume optimization"""
    
    def __init__(self):
        super().__init__("Finance")
        
        self.priority_keywords = [
            # Regulations & Compliance
            'sox', 'sox compliance', 'basel iii', 'dodd-frank', 'mifid', 'gdpr',
            'risk management', 'regulatory compliance', 'audit', 'internal controls',
            # Financial Analysis
            'financial modeling', 'valuation', 'dcf', 'financial analysis', 'budgeting',
            'forecasting', 'variance analysis', 'financial reporting', 'gaap',
            # Risk & Trading
            'market risk', 'credit risk', 'operational risk', 'var', 'stress testing',
            'portfolio management', 'trading', 'derivatives', 'fixed income',
            # Technology in Finance
            'fintech', 'algorithmic trading', 'blockchain', 'cryptocurrency', 'robo-advisor',
            'payment systems', 'digital banking', 'regulatory technology', 'regtech'
        ]
        
        self.language_patterns = {
            'weak_to_strong': {
                'managed money': 'managed investment portfolio of',
                'reduced costs': 'optimized operational efficiency, reducing costs by',
                'improved process': 'streamlined financial processes, improving efficiency by',
                'handled compliance': 'ensured regulatory compliance across',
                'worked with data': 'analyzed complex financial datasets'
            },
            'impact_verbs': [
                'optimized', 'streamlined', 'implemented', 'managed', 'analyzed',
                'forecasted', 'mitigated', 'executed', 'structured', 'negotiated'
            ]
        }
        
        self.metric_types = [
            'portfolio value managed ($)',
            'cost reduction (%)',
            'revenue increase ($)',
            'risk reduction (%)',
            'process efficiency improvement (%)',
            'compliance score (%)',
            'audit findings reduced',
            'deal size ($)',
            'client assets under management'
        ]
    
    def optimize_for_industry(self, resume_content: str, job_requirements: Dict = None) -> OptimizationResult:
        """Optimize resume for finance industry"""
        
        keyword_score_before = self.calculate_keyword_density(resume_content, self.priority_keywords)
        
        improvements_made = []
        optimized_content = resume_content
        
        # Finance-specific optimizations
        optimized_content, lang_improvements = self._enhance_finance_language(optimized_content)
        improvements_made.extend(lang_improvements)
        
        optimized_content, metric_improvements = self._quantify_financial_impact(optimized_content)
        improvements_made.extend(metric_improvements)
        
        optimized_content, compliance_improvements = self._emphasize_compliance_experience(optimized_content)
        improvements_made.extend(compliance_improvements)
        
        keyword_score_after = self.calculate_keyword_density(optimized_content, self.priority_keywords)
        
        recommendations = self._generate_finance_recommendations(optimized_content)
        
        return OptimizationResult(
            industry="Finance",
            optimized_content=optimized_content,
            improvements_made=improvements_made,
            keyword_score_before=keyword_score_before,
            keyword_score_after=keyword_score_after,
            language_enhancement_score=self._calculate_language_score(optimized_content),
            industry_alignment_score=self._calculate_finance_alignment_score(optimized_content),
            recommendations=recommendations
        )
    
    def _enhance