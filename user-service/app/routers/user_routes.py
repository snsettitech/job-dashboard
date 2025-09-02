"""
User Management Routes
Handles user profile management, preferences, and user operations
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.schemas import (
    UserProfileUpdateRequest, ExtendedProfileUpdateRequest,
    UserPreferenceUpdateRequest, UserSearchRequest, UserListResponse,
    UserResponse, UserProfileResponse, UserPreferenceResponse,
    BaseResponse, ErrorResponse
)
from ..services.user_service import UserService
from ..utils.auth import get_current_user, get_current_active_user, get_current_verified_user
from ..models.user_models import User, UserProfile, UserPreference

router = APIRouter(prefix="/users", tags=["User Management"])

@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's profile"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    profile_data: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    try:
        updated_user = UserService.update_user_profile(db, str(current_user.id), profile_data)
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )

@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_extended_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's extended profile"""
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Extended profile not found"
            )
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get extended profile: {str(e)}"
        )

@router.put("/me/profile", response_model=UserProfileResponse)
async def update_my_extended_profile(
    profile_data: ExtendedProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's extended profile"""
    try:
        updated_profile = UserService.create_or_update_extended_profile(
            db, str(current_user.id), profile_data
        )
        return updated_profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extended profile update failed: {str(e)}"
        )

@router.get("/me/preferences", response_model=UserPreferenceResponse)
async def get_my_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's preferences"""
    try:
        preferences = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User preferences not found"
            )
        return preferences
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preferences: {str(e)}"
        )

@router.put("/me/preferences", response_model=UserPreferenceResponse)
async def update_my_preferences(
    preferences_data: UserPreferenceUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's preferences"""
    try:
        updated_preferences = UserService.create_or_update_preferences(
            db, str(current_user.id), preferences_data
        )
        return updated_preferences
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preferences update failed: {str(e)}"
        )

@router.get("/me/stats", response_model=dict)
async def get_my_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's statistics"""
    try:
        stats = UserService.get_user_stats(db, str(current_user.id))
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user stats: {str(e)}"
        )

@router.delete("/me", response_model=BaseResponse)
async def delete_my_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete current user's account"""
    try:
        UserService.delete_user(db, str(current_user.id))
        return BaseResponse(
            message="Account deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account deletion failed: {str(e)}"
        )

# Admin routes (require premium or admin access)
@router.get("/search", response_model=UserListResponse)
async def search_users(
    query: Optional[str] = Query(None, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Search users (premium feature)"""
    try:
        if not current_user.is_premium:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Premium subscription required for user search"
            )
        
        search_request = UserSearchRequest(
            query=query,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        result = UserService.search_users(db, search_request)
        
        return UserListResponse(
            users=result["users"],
            total_count=result["total_count"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
            message="User search completed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User search failed: {str(e)}"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get user by ID (premium feature)"""
    try:
        if not current_user.is_premium:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Premium subscription required to view other users"
            )
        
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )

@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get user's extended profile (premium feature)"""
    try:
        if not current_user.is_premium:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Premium subscription required to view other users"
            )
        
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}"
        )

@router.get("/{user_id}/preferences", response_model=UserPreferenceResponse)
async def get_user_preferences(
    user_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get user's preferences (premium feature)"""
    try:
        if not current_user.is_premium:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Premium subscription required to view other users"
            )
        
        preferences = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User preferences not found"
            )
        
        return preferences
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user preferences: {str(e)}"
        )

# Subscription management routes
@router.post("/me/upgrade", response_model=UserResponse)
async def upgrade_to_premium(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Upgrade user to premium subscription"""
    try:
        if current_user.is_premium:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already premium"
            )
        
        upgraded_user = UserService.upgrade_to_premium(db, str(current_user.id))
        return upgraded_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upgrade failed: {str(e)}"
        )

@router.post("/me/downgrade", response_model=UserResponse)
async def downgrade_to_basic(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Downgrade user to basic subscription"""
    try:
        if not current_user.is_premium:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already basic"
            )
        
        downgraded_user = UserService.downgrade_to_basic(db, str(current_user.id))
        return downgraded_user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Downgrade failed: {str(e)}"
        )

# Health check route
@router.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "user-service",
        "version": "1.0.0"
    }

