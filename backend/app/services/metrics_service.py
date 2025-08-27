# backend/app/services/metrics_service.py - Metrics Collection Service
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import asyncio
from contextlib import asynccontextmanager

@dataclass
class MetricEvent:
    """Individual metric event"""
    timestamp: str
    event_type: str
    user_id: Optional[str]
    session_id: Optional[str]
    data: Dict[str, Any]
    duration_ms: Optional[float] = None

@dataclass
class MetricsSummary:
    """Aggregated metrics summary"""
    total_events: int
    unique_users: int
    unique_sessions: int
    avg_duration_ms: float
    top_events: List[Dict[str, Any]]
    time_range: Dict[str, str]

class MetricsService:
    """Service for collecting and analyzing application metrics"""
    
    def __init__(self, storage_path: str = "data/metrics"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.current_file = self.storage_path / f"metrics_{datetime.now().strftime('%Y%m%d')}.jsonl"
        self._write_lock = asyncio.Lock()  # Add file write lock
        
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()
    
    async def record_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        duration_ms: Optional[float] = None
    ) -> None:
        """Record a metric event"""
        event = MetricEvent(
            timestamp=self._get_current_timestamp(),
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            data=data,
            duration_ms=duration_ms
        )
        
        # Write to file (append mode) with lock
        async with self._write_lock:
            try:
                with open(self.current_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(asdict(event)) + '\n')
            except Exception as e:
                print(f"Error writing metric: {e}")
    
    @asynccontextmanager
    async def time_operation(
        self,
        event_type: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Context manager to time operations"""
        start_time = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            await self.record_event(
                event_type=event_type,
                data=data,
                user_id=user_id,
                session_id=session_id,
                duration_ms=duration_ms
            )
    
    async def get_metrics_summary(
        self,
        days_back: int = 7,
        event_types: Optional[List[str]] = None
    ) -> MetricsSummary:
        """Get aggregated metrics summary"""
        events = await self._load_events(days_back)
        
        if event_types:
            events = [e for e in events if e.event_type in event_types]
        
        if not events:
            return MetricsSummary(
                total_events=0,
                unique_users=0,
                unique_sessions=0,
                avg_duration_ms=0.0,
                top_events=[],
                time_range={
                    "start": (datetime.now() - timedelta(days=days_back)).isoformat(),
                    "end": datetime.now().isoformat()
                }
            )
        
        # Calculate metrics
        unique_users = len(set(e.user_id for e in events if e.user_id))
        unique_sessions = len(set(e.session_id for e in events if e.session_id))
        
        durations = [e.duration_ms for e in events if e.duration_ms is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        
        # Top events by frequency
        event_counts = {}
        for event in events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        top_events = [
            {"event_type": event_type, "count": count}
            for event_type, count in sorted(event_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return MetricsSummary(
            total_events=len(events),
            unique_users=unique_users,
            unique_sessions=unique_sessions,
            avg_duration_ms=avg_duration,
            top_events=top_events,
            time_range={
                "start": (datetime.now() - timedelta(days=days_back)).isoformat(),
                "end": datetime.now().isoformat()
            }
        )
    
    async def _load_events(self, days_back: int) -> List[MetricEvent]:
        """Load events from the last N days"""
        events = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Get all metric files in date range
        for i in range(days_back + 1):
            date = datetime.now() - timedelta(days=i)
            file_path = self.storage_path / f"metrics_{date.strftime('%Y%m%d')}.jsonl"
            
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                event_data = json.loads(line)
                                event = MetricEvent(**event_data)
                                
                                # Check if event is within time range
                                event_time = datetime.fromisoformat(event.timestamp)
                                if event_time >= cutoff_date:
                                    events.append(event)
                except Exception as e:
                    print(f"Error loading metrics from {file_path}: {e}")
        
        return events
    
    async def get_user_metrics(self, user_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Get metrics for a specific user"""
        events = await self._load_events(days_back)
        user_events = [e for e in events if e.user_id == user_id]
        
        if not user_events:
            return {
                "user_id": user_id,
                "total_events": 0,
                "sessions": 0,
                "avg_duration_ms": 0.0,
                "activity": []
            }
        
        sessions = len(set(e.session_id for e in user_events if e.session_id))
        durations = [e.duration_ms for e in user_events if e.duration_ms is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        
        # Activity by day
        activity_by_day = {}
        for event in user_events:
            day = event.timestamp[:10]  # YYYY-MM-DD
            activity_by_day[day] = activity_by_day.get(day, 0) + 1
        
        activity = [
            {"date": date, "events": count}
            for date, count in sorted(activity_by_day.items())
        ]
        
        return {
            "user_id": user_id,
            "total_events": len(user_events),
            "sessions": sessions,
            "avg_duration_ms": avg_duration,
            "activity": activity
        }

# Global metrics service instance
metrics_service = MetricsService()

# Common metric recording functions
async def record_api_call(endpoint: str, method: str, status_code: int, duration_ms: float, user_id: str = None):
    """Record API call metrics"""
    await metrics_service.record_event(
        event_type="api_call",
        data={
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code
        },
        user_id=user_id,
        duration_ms=duration_ms
    )

async def record_resume_optimization(user_id: str, job_title: str, success: bool, duration_ms: float):
    """Record resume optimization metrics"""
    await metrics_service.record_event(
        event_type="resume_optimization",
        data={
            "job_title": job_title,
            "success": success
        },
        user_id=user_id,
        duration_ms=duration_ms
    )

async def record_job_match(user_id: str, match_score: float, job_type: str):
    """Record job matching metrics"""
    await metrics_service.record_event(
        event_type="job_match",
        data={
            "match_score": match_score,
            "job_type": job_type
        },
        user_id=user_id
    )

async def record_user_action(user_id: str, action: str, data: Dict[str, Any] = None):
    """Record general user action"""
    await metrics_service.record_event(
        event_type="user_action",
        data={
            "action": action,
            **(data or {})
        },
        user_id=user_id
    )
