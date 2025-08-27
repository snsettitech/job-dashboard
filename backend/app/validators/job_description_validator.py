# backend/app/validators/job_description_validator.py
"""
Job Description Validation Module

Provides comprehensive validation for job descriptions to ensure they contain
meaningful professional content and reject gibberish, spam, or insufficient content.
"""

import re
import openai
import os
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import asyncio


@dataclass
class ValidationResult:
    """Result of job description validation"""
    is_valid: bool
    error_message: Optional[str] = None
    word_count: int = 0
    professional_terms_found: int = 0
    confidence_score: float = 0.0
    validation_details: Dict = None


class JobDescriptionValidator:
    """Comprehensive job description validation with AI-powered semantic analysis"""
    
    def __init__(self):
        self.client = None  # Initialize lazily
        
        # Professional job-related terms that should appear in legitimate job descriptions
        self.professional_terms = {
            'role_terms': ['position', 'role', 'job', 'opportunity', 'career', 'employment'],
            'requirement_terms': ['requirements', 'qualifications', 'skills', 'experience', 'education'],
            'responsibility_terms': ['responsibilities', 'duties', 'tasks', 'manage', 'develop', 'lead'],
            'company_terms': ['company', 'organization', 'team', 'department', 'business'],
            'skill_terms': ['technical', 'analytical', 'communication', 'leadership', 'problem-solving'],
            'experience_terms': ['years', 'background', 'expertise', 'knowledge', 'proficiency']
        }
        
        # Minimum requirements
        self.min_word_count = 50
        self.min_professional_terms = 5
        self.min_confidence_threshold = 0.7

    def _get_client(self):
        """Lazy initialization of OpenAI client"""
        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise Exception("OpenAI API key not configured")
            self.client = openai.OpenAI(api_key=api_key)
        return self.client
    
    async def validate_job_description(self, job_description: str) -> ValidationResult:
        """
        Comprehensive validation of job description
        Returns ValidationResult with detailed analysis
        """
        if not job_description or not job_description.strip():
            return ValidationResult(
                is_valid=False,
                error_message="Job description cannot be empty",
                validation_details={"error_type": "EMPTY_INPUT"}
            )
        
        job_description = job_description.strip()
        
        # Step 1: Basic length validation
        length_result = self.validate_minimum_length(job_description)
        if not length_result.is_valid:
            return length_result
        
        # Step 2: Gibberish detection
        gibberish_result = self.detect_gibberish(job_description)
        if not gibberish_result.is_valid:
            return gibberish_result
        
        # Step 3: Professional content validation
        professional_result = self.validate_professional_content(job_description)
        if not professional_result.is_valid:
            return professional_result
        
        # Step 4: AI-powered semantic analysis
        semantic_result = await self.semantic_content_analysis(job_description)
        if not semantic_result.is_valid:
            return semantic_result
        
        # All validations passed
        return ValidationResult(
            is_valid=True,
            word_count=len(job_description.split()),
            professional_terms_found=professional_result.professional_terms_found,
            confidence_score=semantic_result.confidence_score,
            validation_details={
                "validation_type": "COMPREHENSIVE_PASS",
                "length_check": "PASSED",
                "gibberish_check": "PASSED", 
                "professional_content_check": "PASSED",
                "semantic_analysis": "PASSED",
                "ai_confidence": semantic_result.confidence_score
            }
        )
    
    def validate_minimum_length(self, job_description: str) -> ValidationResult:
        """Validate minimum word count and meaningful content"""
        words = job_description.split()
        word_count = len(words)
        
        if word_count < self.min_word_count:
            return ValidationResult(
                is_valid=False,
                error_message=f"Job description contains insufficient content (found {word_count} words, minimum {self.min_word_count} required)",
                word_count=word_count,
                validation_details={
                    "error_type": "INSUFFICIENT_LENGTH",
                    "required_words": self.min_word_count,
                    "actual_words": word_count
                }
            )
        
        return ValidationResult(is_valid=True, word_count=word_count)
    
    def detect_gibberish(self, job_description: str) -> ValidationResult:
        """Detect gibberish, repeated characters, keyboard mashing, and spam"""
        text = job_description.lower()
        
        # Check for excessive repeated characters (3+ consecutive identical chars)
        repeated_char_pattern = r'(.)\1{2,}'
        repeated_matches = re.findall(repeated_char_pattern, text)
        if repeated_matches:
            return ValidationResult(
                is_valid=False,
                error_message="Job description appears to contain gibberish (repeated characters detected)",
                validation_details={
                    "error_type": "GIBBERISH_REPEATED_CHARS",
                    "repeated_patterns": repeated_matches[:5]  # Show first 5 patterns
                }
            )
        
        # Check for keyboard mashing patterns
        keyboard_patterns = [
            r'qwerty|asdf|zxcv',  # Common keyboard sequences
            r'123456|abcdef',      # Sequential patterns
            r'aaaaa|bbbbb|ccccc'   # Single character repetition
        ]
        
        for pattern in keyboard_patterns:
            if re.search(pattern, text):
                return ValidationResult(
                    is_valid=False,
                    error_message="Job description appears to be keyboard mashing or spam",
                    validation_details={
                        "error_type": "GIBBERISH_KEYBOARD_MASHING",
                        "detected_pattern": pattern
                    }
                )
        
        # Check for excessive non-alphabetic characters
        alpha_chars = sum(1 for c in text if c.isalpha())
        total_chars = len(text.replace(' ', ''))
        if total_chars > 0 and (alpha_chars / total_chars) < 0.7:
            return ValidationResult(
                is_valid=False,
                error_message="Job description contains too many non-alphabetic characters",
                validation_details={
                    "error_type": "GIBBERISH_NON_ALPHA",
                    "alpha_ratio": alpha_chars / total_chars
                }
            )
        
        return ValidationResult(is_valid=True)
    
    def validate_professional_content(self, job_description: str) -> ValidationResult:
        """Validate presence of professional job-related terms"""
        text = job_description.lower()
        
        # Count professional terms found
        terms_found = []
        for category, terms in self.professional_terms.items():
            for term in terms:
                if term in text:
                    terms_found.append(f"{category}:{term}")
        
        professional_terms_count = len(terms_found)
        
        if professional_terms_count < self.min_professional_terms:
            return ValidationResult(
                is_valid=False,
                error_message=f"Job description lacks professional content (found {professional_terms_count} professional terms, minimum {self.min_professional_terms} required)",
                professional_terms_found=professional_terms_count,
                validation_details={
                    "error_type": "INSUFFICIENT_PROFESSIONAL_CONTENT",
                    "required_terms": self.min_professional_terms,
                    "found_terms": professional_terms_count,
                    "terms_found": terms_found[:10]  # Show first 10 terms found
                }
            )
        
        return ValidationResult(
            is_valid=True, 
            professional_terms_found=professional_terms_count,
            validation_details={"terms_found": terms_found}
        )
    
    async def semantic_content_analysis(self, job_description: str) -> ValidationResult:
        """Use OpenAI to verify the text describes an actual job opportunity"""
        try:
            analysis_prompt = f"""
You are an expert HR analyst. Analyze this text and determine if it describes a legitimate job opportunity.

Text to analyze:
"{job_description}"

Evaluate based on these criteria:
1. Does it describe an actual job position or role?
2. Does it contain meaningful job requirements or responsibilities?
3. Is it coherent and professionally written?
4. Does it provide enough information for a candidate to understand the role?

Return your analysis as JSON with this exact structure:
{{
    "is_legitimate_job": true/false,
    "confidence_score": 0.0-1.0,
    "reasoning": "Brief explanation of your assessment",
    "missing_elements": ["list", "of", "missing", "key", "elements"],
    "professional_quality": "high/medium/low"
}}
"""

            client = self._get_client()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert HR analyst who evaluates job descriptions for legitimacy and quality. Always return valid JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            analysis = json.loads(response.choices[0].message.content.strip())
            
            is_legitimate = analysis.get("is_legitimate_job", False)
            confidence = analysis.get("confidence_score", 0.0)
            
            if not is_legitimate or confidence < self.min_confidence_threshold:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Job description does not appear to describe a legitimate job opportunity (AI confidence: {confidence:.1%})",
                    confidence_score=confidence,
                    validation_details={
                        "error_type": "SEMANTIC_ANALYSIS_FAILED",
                        "ai_reasoning": analysis.get("reasoning", ""),
                        "missing_elements": analysis.get("missing_elements", []),
                        "professional_quality": analysis.get("professional_quality", "unknown"),
                        "confidence_score": confidence
                    }
                )
            
            return ValidationResult(
                is_valid=True,
                confidence_score=confidence,
                validation_details={
                    "semantic_analysis": "PASSED",
                    "ai_reasoning": analysis.get("reasoning", ""),
                    "professional_quality": analysis.get("professional_quality", "unknown"),
                    "confidence_score": confidence
                }
            )
            
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                error_message="Failed to analyze job description content (AI response parsing error)",
                validation_details={
                    "error_type": "AI_RESPONSE_PARSING_ERROR",
                    "error_details": str(e)
                }
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message="Failed to analyze job description content (AI service error)",
                validation_details={
                    "error_type": "AI_SERVICE_ERROR",
                    "error_details": str(e)
                }
            )
