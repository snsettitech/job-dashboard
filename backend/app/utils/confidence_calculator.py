# backend/app/utils/confidence_calculator.py
"""
Confidence Calculator Module

Provides comprehensive confidence scoring for AI-generated results
based on input quality, processing success, and output validation.
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import statistics


@dataclass
class ConfidenceFactors:
    """Factors that contribute to confidence scoring"""
    input_quality: float = 0.0
    processing_success: float = 0.0
    output_quality: float = 0.0
    consistency: float = 0.0
    ai_response_quality: float = 0.0
    validation_passed: bool = False


class ConfidenceCalculator:
    """Calculate confidence scores for AI-generated results"""
    
    def __init__(self):
        # Confidence weights for different factors
        self.weights = {
            'input_quality': 0.25,      # Quality of input data
            'processing_success': 0.20,  # Success of AI processing
            'output_quality': 0.25,     # Quality of AI output
            'consistency': 0.15,        # Consistency across multiple runs
            'ai_response_quality': 0.15  # Quality of AI responses
        }
        
        # Confidence thresholds
        self.high_confidence_threshold = 85.0
        self.medium_confidence_threshold = 65.0
        self.low_confidence_threshold = 40.0
    
    def calculate_input_quality_score(self, 
                                    word_count: int,
                                    professional_terms_found: int,
                                    semantic_validation_score: float,
                                    validation_details: Dict) -> float:
        """Calculate input quality score (0-100)"""
        
        # Word count factor (0-30 points)
        word_score = min(30, (word_count / 100) * 30)  # Full points at 100+ words
        
        # Professional terms factor (0-25 points)
        terms_score = min(25, professional_terms_found * 2.5)  # Full points at 10+ terms
        
        # Semantic validation factor (0-35 points)
        semantic_score = semantic_validation_score * 35
        
        # Validation details factor (0-10 points)
        details_score = 10
        if validation_details.get("error_type"):
            details_score = 0
        elif validation_details.get("professional_quality") == "low":
            details_score = 3
        elif validation_details.get("professional_quality") == "medium":
            details_score = 7
        
        total_score = word_score + terms_score + semantic_score + details_score
        return min(100, max(0, total_score))
    
    def calculate_processing_success_score(self,
                                         total_ai_calls: int,
                                         successful_ai_calls: int,
                                         processing_time_ms: int,
                                         fallback_used: bool) -> float:
        """Calculate processing success score (0-100)"""
        
        # AI calls success rate (0-40 points)
        if total_ai_calls > 0:
            success_rate = successful_ai_calls / total_ai_calls
            success_score = success_rate * 40
        else:
            success_score = 0
        
        # Processing time factor (0-30 points)
        # Realistic AI processing should take 1-15 seconds
        if processing_time_ms < 500:  # Too fast, likely cached/mock
            time_score = 5
        elif processing_time_ms < 1000:  # Very fast, possibly cached
            time_score = 15
        elif processing_time_ms <= 15000:  # Normal range
            time_score = 30
        elif processing_time_ms <= 30000:  # Slow but acceptable
            time_score = 20
        else:  # Too slow
            time_score = 10
        
        # Fallback penalty (0-30 points)
        fallback_score = 0 if fallback_used else 30
        
        total_score = success_score + time_score + fallback_score
        return min(100, max(0, total_score))
    
    def calculate_output_quality_score(self,
                                     output_data: Dict,
                                     expected_fields: List[str],
                                     content_analysis: Optional[Dict] = None) -> float:
        """Calculate output quality score (0-100)"""
        
        # Field completeness (0-30 points)
        present_fields = sum(1 for field in expected_fields if field in output_data and output_data[field])
        field_score = (present_fields / len(expected_fields)) * 30 if expected_fields else 30
        
        # Content quality (0-40 points)
        content_score = 40
        if content_analysis:
            # Check for specific quality indicators
            if content_analysis.get("has_specific_improvements", False):
                content_score = min(content_score, content_score + 10)
            if content_analysis.get("has_quantified_metrics", False):
                content_score = min(content_score, content_score + 10)
            if content_analysis.get("professional_language", False):
                content_score = min(content_score, content_score + 10)
            if content_analysis.get("actionable_suggestions", False):
                content_score = min(content_score, content_score + 10)
        
        # Data validity (0-30 points)
        validity_score = 30
        
        # Check for placeholder/generic content
        if self._contains_placeholder_content(output_data):
            validity_score -= 15
        
        # Check for realistic scores/percentages
        if not self._has_realistic_metrics(output_data):
            validity_score -= 10
        
        # Check for sufficient detail
        if not self._has_sufficient_detail(output_data):
            validity_score -= 5
        
        total_score = field_score + content_score + validity_score
        return min(100, max(0, total_score))
    
    def calculate_ai_response_quality_score(self,
                                          ai_responses: List[Dict],
                                          response_times: List[float]) -> float:
        """Calculate AI response quality score (0-100)"""
        
        if not ai_responses:
            return 0
        
        # Response completeness (0-30 points)
        complete_responses = sum(1 for resp in ai_responses if self._is_complete_response(resp))
        completeness_score = (complete_responses / len(ai_responses)) * 30
        
        # Response time consistency (0-25 points)
        if len(response_times) > 1:
            time_std = statistics.stdev(response_times)
            avg_time = statistics.mean(response_times)
            consistency_ratio = 1 - (time_std / avg_time) if avg_time > 0 else 0
            time_score = max(0, consistency_ratio * 25)
        else:
            time_score = 20  # Single response gets moderate score
        
        # JSON validity (0-25 points)
        valid_json_responses = sum(1 for resp in ai_responses if self._is_valid_json_response(resp))
        json_score = (valid_json_responses / len(ai_responses)) * 25
        
        # Content specificity (0-20 points)
        specific_responses = sum(1 for resp in ai_responses if self._is_specific_response(resp))
        specificity_score = (specific_responses / len(ai_responses)) * 20
        
        total_score = completeness_score + time_score + json_score + specificity_score
        return min(100, max(0, total_score))
    
    def calculate_overall_confidence(self, factors: ConfidenceFactors) -> Tuple[float, str, Dict]:
        """Calculate overall confidence score and provide detailed breakdown"""
        
        # Calculate weighted score
        weighted_score = (
            factors.input_quality * self.weights['input_quality'] +
            factors.processing_success * self.weights['processing_success'] +
            factors.output_quality * self.weights['output_quality'] +
            factors.consistency * self.weights['consistency'] +
            factors.ai_response_quality * self.weights['ai_response_quality']
        )
        
        # Apply validation bonus/penalty
        if factors.validation_passed:
            weighted_score = min(100, weighted_score + 5)
        else:
            weighted_score = max(0, weighted_score - 10)
        
        # Determine confidence level
        if weighted_score >= self.high_confidence_threshold:
            confidence_level = "high"
        elif weighted_score >= self.medium_confidence_threshold:
            confidence_level = "medium"
        elif weighted_score >= self.low_confidence_threshold:
            confidence_level = "low"
        else:
            confidence_level = "very_low"
        
        # Create detailed breakdown
        breakdown = {
            "overall_score": round(weighted_score, 1),
            "confidence_level": confidence_level,
            "factor_scores": {
                "input_quality": round(factors.input_quality, 1),
                "processing_success": round(factors.processing_success, 1),
                "output_quality": round(factors.output_quality, 1),
                "consistency": round(factors.consistency, 1),
                "ai_response_quality": round(factors.ai_response_quality, 1)
            },
            "weighted_contributions": {
                "input_quality": round(factors.input_quality * self.weights['input_quality'], 1),
                "processing_success": round(factors.processing_success * self.weights['processing_success'], 1),
                "output_quality": round(factors.output_quality * self.weights['output_quality'], 1),
                "consistency": round(factors.consistency * self.weights['consistency'], 1),
                "ai_response_quality": round(factors.ai_response_quality * self.weights['ai_response_quality'], 1)
            },
            "validation_passed": factors.validation_passed
        }
        
        return weighted_score, confidence_level, breakdown
    
    def get_confidence_interval(self, confidence_score: float, sample_size: int = 1) -> Tuple[float, float]:
        """Calculate confidence interval for the score"""
        
        # Base margin of error depends on confidence score and sample size
        base_margin = 15 - (confidence_score / 100) * 10  # Higher confidence = lower margin
        
        # Adjust for sample size (more AI calls = more confidence)
        sample_adjustment = max(0.5, 1 / (sample_size ** 0.5))
        margin = base_margin * sample_adjustment
        
        lower_bound = max(0, confidence_score - margin)
        upper_bound = min(100, confidence_score + margin)
        
        return lower_bound, upper_bound
    
    def _contains_placeholder_content(self, output_data: Dict) -> bool:
        """Check if output contains placeholder or generic content"""
        placeholder_indicators = [
            "placeholder", "example", "sample", "template",
            "lorem ipsum", "test", "mock", "fallback",
            "temporarily unavailable", "not available"
        ]
        
        content_str = json.dumps(output_data).lower()
        return any(indicator in content_str for indicator in placeholder_indicators)
    
    def _has_realistic_metrics(self, output_data: Dict) -> bool:
        """Check if metrics/scores in output are realistic"""
        
        # Look for percentage improvements
        percentage_pattern = r'(\+?\d+)%'
        percentages = re.findall(percentage_pattern, str(output_data))
        
        for pct in percentages:
            value = int(pct.replace('+', ''))
            # Unrealistic if improvement is too high or too low
            if value > 100 or value < 1:
                return False
        
        # Look for match scores
        if 'match_scores' in output_data:
            scores = output_data['match_scores']
            if isinstance(scores, dict):
                for score in scores.values():
                    if isinstance(score, (int, float)):
                        if score < 0 or score > 1:
                            return False
        
        return True
    
    def _has_sufficient_detail(self, output_data: Dict) -> bool:
        """Check if output has sufficient detail and specificity"""
        
        # Check for lists with meaningful content
        for key, value in output_data.items():
            if isinstance(value, list) and len(value) > 0:
                # Check if list items are sufficiently detailed
                for item in value:
                    if isinstance(item, str) and len(item.split()) < 3:
                        return False
        
        # Check for meaningful text content
        text_fields = ['optimized_resume', 'recommendation', 'optimization_summary']
        for field in text_fields:
            if field in output_data:
                content = output_data[field]
                if isinstance(content, str) and len(content.split()) < 10:
                    return False
        
        return True
    
    def _is_complete_response(self, response: Dict) -> bool:
        """Check if AI response is complete"""
        return bool(response and len(str(response)) > 50)
    
    def _is_valid_json_response(self, response: Dict) -> bool:
        """Check if response is valid JSON structure"""
        try:
            json.dumps(response)
            return True
        except:
            return False
    
    def _is_specific_response(self, response: Dict) -> bool:
        """Check if response contains specific, non-generic content"""
        generic_terms = ['good', 'better', 'improve', 'enhance', 'optimize', 'professional']
        content_str = json.dumps(response).lower()
        
        # Count specific vs generic terms
        specific_indicators = ['quantified', 'metrics', 'specific', 'detailed', 'particular']
        specific_count = sum(1 for term in specific_indicators if term in content_str)
        generic_count = sum(1 for term in generic_terms if term in content_str)
        
        return specific_count >= generic_count


# Global confidence calculator instance
confidence_calculator = ConfidenceCalculator()
