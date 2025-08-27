# backend/app/services/ai_processing_tracker.py
"""
AI Processing Tracker Module

Provides comprehensive tracking and logging of all AI interactions to ensure
transparency and verify genuine AI processing vs fallback data.
"""

import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class AICall:
    """Record of a single AI API call"""
    call_id: str
    model: str
    operation: str  # 'embedding', 'chat_completion', 'analysis'
    start_time: float
    end_time: Optional[float] = None
    tokens_used: Optional[int] = None
    success: bool = False
    error_message: Optional[str] = None
    response_quality: Optional[str] = None  # 'high', 'medium', 'low'


@dataclass
class ProcessingSession:
    """Complete processing session with all AI calls"""
    session_id: str
    operation_type: str  # 'job_match', 'resume_optimization', 'validation'
    start_time: float
    end_time: Optional[float] = None
    ai_calls: List[AICall] = None
    input_quality_score: Optional[float] = None
    output_confidence_score: Optional[float] = None
    fallback_used: bool = False
    processing_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.ai_calls is None:
            self.ai_calls = []
        if self.processing_metadata is None:
            self.processing_metadata = {}


class AIProcessingTracker:
    """Tracks all AI processing for transparency and verification"""
    
    def __init__(self):
        self.active_sessions: Dict[str, ProcessingSession] = {}
        self.completed_sessions: List[ProcessingSession] = []
        self.max_completed_sessions = 1000  # Keep last 1000 sessions in memory
    
    def start_processing_session(self, operation_type: str) -> str:
        """Start a new processing session and return session ID"""
        session_id = str(uuid.uuid4())
        session = ProcessingSession(
            session_id=session_id,
            operation_type=operation_type,
            start_time=time.time()
        )
        self.active_sessions[session_id] = session
        
        logger.info(f"Started AI processing session {session_id} for {operation_type}")
        return session_id
    
    def start_ai_call(self, session_id: str, model: str, operation: str) -> str:
        """Start tracking an AI API call"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        call_id = str(uuid.uuid4())
        ai_call = AICall(
            call_id=call_id,
            model=model,
            operation=operation,
            start_time=time.time()
        )
        
        self.active_sessions[session_id].ai_calls.append(ai_call)
        logger.debug(f"Started AI call {call_id} for {operation} using {model}")
        return call_id
    
    def complete_ai_call(self, session_id: str, call_id: str, 
                        success: bool = True, tokens_used: Optional[int] = None,
                        error_message: Optional[str] = None,
                        response_quality: Optional[str] = None):
        """Mark an AI call as completed"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        for ai_call in session.ai_calls:
            if ai_call.call_id == call_id:
                ai_call.end_time = time.time()
                ai_call.success = success
                ai_call.tokens_used = tokens_used
                ai_call.error_message = error_message
                ai_call.response_quality = response_quality
                
                duration = ai_call.end_time - ai_call.start_time
                logger.debug(f"Completed AI call {call_id} in {duration:.2f}s, success: {success}")
                break
    
    def set_input_quality_score(self, session_id: str, score: float):
        """Set the input quality score for the session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].input_quality_score = score
    
    def set_output_confidence_score(self, session_id: str, score: float):
        """Set the output confidence score for the session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].output_confidence_score = score
    
    def mark_fallback_used(self, session_id: str, fallback_reason: str):
        """Mark that fallback data was used instead of AI processing"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.fallback_used = True
            session.processing_metadata["fallback_reason"] = fallback_reason
            logger.warning(f"Fallback used in session {session_id}: {fallback_reason}")
    
    def add_metadata(self, session_id: str, key: str, value: Any):
        """Add metadata to the processing session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].processing_metadata[key] = value
    
    def complete_processing_session(self, session_id: str) -> ProcessingSession:
        """Complete a processing session and return the session data"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        session.end_time = time.time()
        
        # Calculate session statistics
        total_duration = session.end_time - session.start_time
        successful_calls = sum(1 for call in session.ai_calls if call.success)
        total_calls = len(session.ai_calls)
        total_tokens = sum(call.tokens_used or 0 for call in session.ai_calls)
        
        session.processing_metadata.update({
            "total_duration_ms": int(total_duration * 1000),
            "successful_ai_calls": successful_calls,
            "total_ai_calls": total_calls,
            "total_tokens_used": total_tokens,
            "ai_success_rate": successful_calls / total_calls if total_calls > 0 else 0
        })
        
        # Move to completed sessions
        del self.active_sessions[session_id]
        self.completed_sessions.append(session)
        
        # Maintain memory limit
        if len(self.completed_sessions) > self.max_completed_sessions:
            self.completed_sessions = self.completed_sessions[-self.max_completed_sessions:]
        
        logger.info(f"Completed processing session {session_id} in {total_duration:.2f}s with {successful_calls}/{total_calls} successful AI calls")
        return session
    
    def get_processing_metadata(self, session_id: str) -> Dict[str, Any]:
        """Get processing metadata for inclusion in API responses"""
        # Check active sessions first
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
        else:
            # Check completed sessions
            session = None
            for completed_session in reversed(self.completed_sessions):
                if completed_session.session_id == session_id:
                    session = completed_session
                    break
            
            if not session:
                return {"error": "Session not found"}
        
        # Calculate current statistics
        successful_calls = sum(1 for call in session.ai_calls if call.success)
        total_calls = len(session.ai_calls)
        models_used = list(set(call.model for call in session.ai_calls))
        
        processing_time_ms = 0
        if session.end_time:
            processing_time_ms = int((session.end_time - session.start_time) * 1000)
        else:
            processing_time_ms = int((time.time() - session.start_time) * 1000)
        
        return {
            "processing_id": session_id,
            "ai_models_used": models_used,
            "processing_time_ms": processing_time_ms,
            "ai_calls_made": total_calls,
            "successful_ai_calls": successful_calls,
            "fallback_used": session.fallback_used,
            "input_quality_score": session.input_quality_score,
            "confidence_score": session.output_confidence_score,
            "operation_type": session.operation_type,
            **session.processing_metadata
        }
    
    def calculate_confidence_score(self, session_id: str) -> float:
        """Calculate overall confidence score based on processing quality"""
        if session_id not in self.active_sessions:
            return 0.0
        
        session = self.active_sessions[session_id]
        
        # Base confidence factors
        confidence_factors = []
        
        # Input quality factor (0-100)
        if session.input_quality_score is not None:
            confidence_factors.append(session.input_quality_score)
        
        # AI processing success rate factor
        if session.ai_calls:
            successful_calls = sum(1 for call in session.ai_calls if call.success)
            success_rate = successful_calls / len(session.ai_calls)
            confidence_factors.append(success_rate * 100)
        
        # Response quality factor
        quality_scores = []
        for call in session.ai_calls:
            if call.response_quality == "high":
                quality_scores.append(90)
            elif call.response_quality == "medium":
                quality_scores.append(70)
            elif call.response_quality == "low":
                quality_scores.append(40)
        
        if quality_scores:
            confidence_factors.append(sum(quality_scores) / len(quality_scores))
        
        # Fallback penalty
        if session.fallback_used:
            confidence_factors.append(30)  # Heavy penalty for fallback usage
        
        # Calculate weighted average
        if confidence_factors:
            confidence_score = sum(confidence_factors) / len(confidence_factors)
            return min(100, max(0, confidence_score))
        
        return 50.0  # Default moderate confidence
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a comprehensive summary of the processing session"""
        metadata = self.get_processing_metadata(session_id)
        confidence = self.calculate_confidence_score(session_id)
        
        return {
            "session_summary": {
                "processing_id": session_id,
                "confidence_score": round(confidence, 1),
                "processing_time_ms": metadata.get("processing_time_ms", 0),
                "ai_models_used": metadata.get("ai_models_used", []),
                "genuine_ai_processing": not metadata.get("fallback_used", True),
                "quality_indicators": {
                    "input_validation_passed": metadata.get("input_quality_score", 0) > 70,
                    "ai_calls_successful": metadata.get("successful_ai_calls", 0) > 0,
                    "no_fallback_used": not metadata.get("fallback_used", True),
                    "processing_time_realistic": metadata.get("processing_time_ms", 0) > 1000  # At least 1 second
                }
            }
        }


# Global tracker instance
ai_tracker = AIProcessingTracker()
