# backend/app/routers/metrics_routes.py - Metrics API Routes
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..services.metrics_service import metrics_service, record_user_action

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

# Request/Response Models
class MetricEventRequest(BaseModel):
    event_type: str
    data: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class MetricsResponse(BaseModel):
    total_events: int
    unique_users: int
    unique_sessions: int
    avg_duration_ms: float
    top_events: List[Dict[str, Any]]
    time_range: Dict[str, str]

# API Endpoints
@router.post("/record")
async def record_metric(request: MetricEventRequest):
    """Record a custom metric event"""
    try:
        await metrics_service.record_event(
            event_type=request.event_type,
            data=request.data,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        return {"status": "success", "message": "Metric recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording metric: {str(e)}")

@router.get("/summary", response_model=MetricsResponse)
async def get_metrics_summary(
    days_back: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    event_types: Optional[str] = Query(None, description="Comma-separated list of event types to filter")
):
    """Get aggregated metrics summary"""
    try:
        event_type_list = None
        if event_types:
            event_type_list = [et.strip() for et in event_types.split(",")]
        
        summary = await metrics_service.get_metrics_summary(
            days_back=days_back,
            event_types=event_type_list
        )
        
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics summary: {str(e)}")

@router.get("/user/{user_id}")
async def get_user_metrics(
    user_id: str,
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back")
):
    """Get metrics for a specific user"""
    try:
        user_metrics = await metrics_service.get_user_metrics(user_id, days_back)
        return user_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user metrics: {str(e)}")

@router.get("/dashboard")
async def get_metrics_dashboard():
    """Get metrics dashboard data"""
    try:
        # Get summary for different time periods
        today = await metrics_service.get_metrics_summary(days_back=1)
        week = await metrics_service.get_metrics_summary(days_back=7)
        month = await metrics_service.get_metrics_summary(days_back=30)
        
        # Calculate growth rates
        def calculate_growth(current: int, previous: int) -> float:
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return ((current - previous) / previous) * 100
        
        dashboard_data = {
            "overview": {
                "today": {
                    "events": today.total_events,
                    "users": today.unique_users,
                    "sessions": today.unique_sessions
                },
                "week": {
                    "events": week.total_events,
                    "users": week.unique_users,
                    "sessions": week.unique_sessions
                },
                "month": {
                    "events": month.total_events,
                    "users": month.unique_users,
                    "sessions": month.unique_sessions
                }
            },
            "top_events": week.top_events[:5],
            "performance": {
                "avg_duration_ms": week.avg_duration_ms,
                "total_operations": week.total_events
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard data: {str(e)}")

@router.post("/track/page-view")
async def track_page_view(
    page: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """Track page view"""
    try:
        await record_user_action(
            user_id=user_id or "anonymous",
            action="page_view",
            data={"page": page, "session_id": session_id}
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking page view: {str(e)}")

@router.post("/track/button-click")
async def track_button_click(
    button_id: str,
    page: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """Track button click"""
    try:
        await record_user_action(
            user_id=user_id or "anonymous",
            action="button_click",
            data={
                "button_id": button_id,
                "page": page,
                "session_id": session_id
            }
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking button click: {str(e)}")

@router.post("/track/feature-usage")
async def track_feature_usage(
    feature: str,
    action: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Track feature usage"""
    try:
        await record_user_action(
            user_id=user_id or "anonymous",
            action="feature_usage",
            data={
                "feature": feature,
                "feature_action": action,
                "session_id": session_id,
                **(metadata or {})
            }
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking feature usage: {str(e)}")

@router.get("/health")
async def metrics_health_check():
    """Health check for metrics service"""
    try:
        # Test recording a metric
        await metrics_service.record_event(
            event_type="health_check",
            data={"status": "ok"},
            user_id="system"
        )
        
        # Test reading metrics
        summary = await metrics_service.get_metrics_summary(days_back=1)
        
        return {
            "status": "healthy",
            "metrics_service": "operational",
            "storage_path": str(metrics_service.storage_path),
            "recent_events": summary.total_events,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
