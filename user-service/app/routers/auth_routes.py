"""
Authentication Routes
Handles user registration, login, token refresh, and password management
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.schemas import (
    UserRegisterRequest, UserLoginRequest, UserLoginResponse,
    TokenRefreshRequest, TokenRefreshResponse, PasswordResetRequest,
    PasswordResetConfirmRequest, BaseResponse, ErrorResponse
)
from ..services.user_service import UserService
from ..utils.auth import (
    AuthService, TokenManager, PasswordManager,
    get_current_user, get_current_active_user
)
from ..models.user_models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=BaseResponse)
async def register_user(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user account"""
    try:
        # Create user
        user = UserService.create_user(db, user_data)
        
        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        
        # TODO: Send verification email
        # For now, just return success
        
        return BaseResponse(
            message="User registered successfully. Please check your email for verification.",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=UserLoginResponse)
async def login_user(
    login_data: UserLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login user and return JWT tokens"""
    try:
        # Authenticate user
        user = AuthService.authenticate_user(db, login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Update last login
        AuthService.update_last_login(db, user)
        
        # Generate tokens
        access_token_data = {"sub": str(user.id), "email": user.email}
        refresh_token_data = {"sub": str(user.id), "email": user.email}
        
        access_token = AuthService.create_access_token(access_token_data)
        refresh_token = AuthService.create_refresh_token(refresh_token_data)
        
        # Get client information
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Store refresh token
        TokenManager.create_refresh_token_record(
            db, str(user.id), refresh_token, client_ip, user_agent
        )
        
        # Create session token for tracking
        session_token = AuthService.create_session_token({"sub": str(user.id)})
        TokenManager.create_session_record(
            db, str(user.id), session_token, client_ip, user_agent
        )
        
        return UserLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60,  # 30 minutes
            user=user,
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = AuthService.verify_token(refresh_data.refresh_token, "refresh")
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if refresh token exists and is not revoked
        from ..models.user_models import RefreshToken
        refresh_token_record = db.query(RefreshToken).filter(
            RefreshToken.token == refresh_data.refresh_token,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        ).first()
        
        if not refresh_token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Get user
        user = UserService.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new access token
        access_token_data = {"sub": str(user.id), "email": user.email}
        access_token = AuthService.create_access_token(access_token_data)
        
        # Update last activity
        AuthService.update_last_activity(db, user)
        
        return TokenRefreshResponse(
            access_token=access_token,
            expires_in=30 * 60,  # 30 minutes
            message="Token refreshed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )

@router.post("/logout", response_model=BaseResponse)
async def logout_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout user and revoke refresh tokens"""
    try:
        # Revoke all refresh tokens for the user
        TokenManager.revoke_all_user_tokens(db, str(current_user.id))
        
        # Revoke all sessions for the user
        UserService.revoke_all_sessions(db, str(current_user.id))
        
        return BaseResponse(
            message="Logged out successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

@router.post("/logout-all", response_model=BaseResponse)
async def logout_all_devices(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout user from all devices"""
    try:
        # Revoke all refresh tokens for the user
        TokenManager.revoke_all_user_tokens(db, str(current_user.id))
        
        # Revoke all sessions for the user
        UserService.revoke_all_sessions(db, str(current_user.id))
        
        return BaseResponse(
            message="Logged out from all devices successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

@router.post("/password-reset-request", response_model=BaseResponse)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    try:
        UserService.request_password_reset(db, reset_request.email)
        
        return BaseResponse(
            message="If the email exists, a password reset link has been sent"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset request failed: {str(e)}"
        )

@router.post("/password-reset-confirm", response_model=BaseResponse)
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirmRequest,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token"""
    try:
        UserService.reset_password(db, reset_confirm.token, reset_confirm.new_password)
        
        return BaseResponse(
            message="Password reset successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )

@router.post("/verify-email-request", response_model=BaseResponse)
async def request_email_verification(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Request email verification"""
    try:
        UserService.request_email_verification(db, str(current_user.id))
        
        return BaseResponse(
            message="Verification email sent successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email verification request failed: {str(e)}"
        )

@router.post("/verify-email", response_model=BaseResponse)
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify email with token"""
    try:
        UserService.verify_email(db, token)
        
        return BaseResponse(
            message="Email verified successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email verification failed: {str(e)}"
        )

@router.get("/me", response_model=dict)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "is_premium": current_user.is_premium,
        "subscription_tier": current_user.subscription_tier,
        "subscription_status": current_user.subscription_status,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login,
        "last_activity": current_user.last_activity
    }

@router.post("/change-password", response_model=BaseResponse)
async def change_password(
    password_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        from ..models.schemas import PasswordChangeRequest
        password_request = PasswordChangeRequest(**password_data)
        
        UserService.change_password(db, str(current_user.id), password_request)
        
        return BaseResponse(
            message="Password changed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password change failed: {str(e)}"
        )

@router.get("/sessions", response_model=dict)
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's active sessions"""
    try:
        sessions = UserService.get_user_sessions(db, str(current_user.id))
        
        return {
            "sessions": [
                {
                    "id": str(session.id),
                    "ip_address": session.ip_address,
                    "user_agent": session.user_agent,
                    "device_type": session.device_type,
                    "browser": session.browser,
                    "os": session.os,
                    "is_active": session.is_active,
                    "expires_at": session.expires_at,
                    "created_at": session.created_at,
                    "last_activity": session.last_activity
                }
                for session in sessions
            ],
            "total_count": len(sessions)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )

@router.delete("/sessions/{session_id}", response_model=BaseResponse)
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Revoke a specific user session"""
    try:
        UserService.revoke_session(db, str(current_user.id), session_id)
        
        return BaseResponse(
            message="Session revoked successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke session: {str(e)}"
        )

