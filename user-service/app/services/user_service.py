"""
User Service Business Logic
Core user management operations and business rules
"""

import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from fastapi import HTTPException, status

from ..models.user_models import (
    User, UserProfile, UserPreference, UserSession,
    RefreshToken, PasswordReset, EmailVerification
)
from ..models.schemas import (
    UserRegisterRequest, UserProfileUpdateRequest, ExtendedProfileUpdateRequest,
    UserPreferenceUpdateRequest, PasswordChangeRequest, UserSearchRequest
)
from ..utils.auth import AuthService, TokenManager, PasswordManager, EmailVerificationManager

class UserService:
    """User service for managing user accounts and profiles"""
    
    @staticmethod
    def create_user(db: Session, user_data: UserRegisterRequest) -> User:
        """Create a new user account"""
        # Check if email already exists
        existing_user = AuthService.get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists (if provided)
        if user_data.username:
            existing_username = AuthService.get_user_by_username(db, user_data.username)
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Hash password
        hashed_password = AuthService.get_password_hash(user_data.password)
        
        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            password_hash=hashed_password,
            is_active=True,
            is_verified=False,
            is_premium=False,
            subscription_tier='basic',
            subscription_status='active'
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def update_user_profile(db: Session, user_id: str, profile_data: UserProfileUpdateRequest) -> User:
        """Update user profile information"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields that are not None
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def create_or_update_extended_profile(db: Session, user_id: str, profile_data: ExtendedProfileUpdateRequest) -> UserProfile:
        """Create or update extended user profile"""
        # Check if user exists
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get existing profile or create new one
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if profile:
            # Update existing profile
            update_data = profile_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(profile, field, value)
            profile.updated_at = datetime.utcnow()
        else:
            # Create new profile
            profile = UserProfile(
                user_id=user_id,
                **profile_data.dict(exclude_unset=True)
            )
            db.add(profile)
        
        db.commit()
        db.refresh(profile)
        
        return profile
    
    @staticmethod
    def create_or_update_preferences(db: Session, user_id: str, preferences_data: UserPreferenceUpdateRequest) -> UserPreference:
        """Create or update user preferences"""
        # Check if user exists
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get existing preferences or create new ones
        preferences = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        
        if preferences:
            # Update existing preferences
            update_data = preferences_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(preferences, field, value)
            preferences.updated_at = datetime.utcnow()
        else:
            # Create new preferences
            preferences = UserPreference(
                user_id=user_id,
                **preferences_data.dict(exclude_unset=True)
            )
            db.add(preferences)
        
        db.commit()
        db.refresh(preferences)
        
        return preferences
    
    @staticmethod
    def change_password(db: Session, user_id: str, password_data: PasswordChangeRequest) -> bool:
        """Change user password"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not AuthService.verify_password(password_data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_password_hash = AuthService.get_password_hash(password_data.new_password)
        user.password_hash = new_password_hash
        user.updated_at = datetime.utcnow()
        
        # Revoke all refresh tokens for security
        TokenManager.revoke_all_user_tokens(db, user_id)
        
        db.commit()
        
        return True
    
    @staticmethod
    def request_password_reset(db: Session, email: str) -> bool:
        """Request password reset"""
        user = UserService.get_user_by_email(db, email)
        if not user:
            # Don't reveal if email exists or not
            return True
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        
        # Create password reset record
        PasswordManager.create_password_reset_token(
            db, user.id, reset_token
        )
        
        # TODO: Send email with reset link
        # For now, just return success
        
        return True
    
    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> bool:
        """Reset password using token"""
        # Verify token
        password_reset = PasswordManager.verify_password_reset_token(db, token)
        if not password_reset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Get user
        user = UserService.get_user_by_id(db, password_reset.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Hash new password
        new_password_hash = AuthService.get_password_hash(new_password)
        user.password_hash = new_password_hash
        user.updated_at = datetime.utcnow()
        
        # Mark token as used
        PasswordManager.mark_password_reset_used(db, token)
        
        # Revoke all refresh tokens for security
        TokenManager.revoke_all_user_tokens(db, user.id)
        
        db.commit()
        
        return True
    
    @staticmethod
    def request_email_verification(db: Session, user_id: str) -> bool:
        """Request email verification"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        
        # Create verification record
        EmailVerificationManager.create_verification_token(
            db, user_id, verification_token
        )
        
        # TODO: Send email with verification link
        # For now, just return success
        
        return True
    
    @staticmethod
    def verify_email(db: Session, token: str) -> bool:
        """Verify email using token"""
        # Verify token
        verification = EmailVerificationManager.verify_email_token(db, token)
        if not verification:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        # Get user
        user = UserService.get_user_by_id(db, verification.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Mark email as verified
        user.is_verified = True
        user.updated_at = datetime.utcnow()
        
        # Mark token as used
        EmailVerificationManager.mark_verification_used(db, token)
        
        db.commit()
        
        return True
    
    @staticmethod
    def search_users(db: Session, search_request: UserSearchRequest) -> Dict[str, Any]:
        """Search users with pagination and filtering"""
        query = db.query(User)
        
        # Apply search filter
        if search_request.query:
            search_term = f"%{search_request.query}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term),
                    User.username.ilike(search_term),
                    User.current_title.ilike(search_term)
                )
            )
        
        # Apply sorting
        if search_request.sort_by:
            sort_column = getattr(User, search_request.sort_by, User.created_at)
            if search_request.sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(User.created_at))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (search_request.page - 1) * search_request.page_size
        users = query.offset(offset).limit(search_request.page_size).all()
        
        # Calculate pagination info
        total_pages = (total_count + search_request.page_size - 1) // search_request.page_size
        
        return {
            "users": users,
            "total_count": total_count,
            "page": search_request.page,
            "page_size": search_request.page_size,
            "total_pages": total_pages
        }
    
    @staticmethod
    def get_user_sessions(db: Session, user_id: str) -> List[UserSession]:
        """Get user's active sessions"""
        sessions = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).order_by(desc(UserSession.created_at)).all()
        
        return sessions
    
    @staticmethod
    def revoke_session(db: Session, user_id: str, session_id: str) -> bool:
        """Revoke a specific user session"""
        session = db.query(UserSession).filter(
            and_(
                UserSession.id == session_id,
                UserSession.user_id == user_id
            )
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session.is_active = False
        db.commit()
        
        return True
    
    @staticmethod
    def revoke_all_sessions(db: Session, user_id: str) -> bool:
        """Revoke all user sessions"""
        sessions = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).all()
        
        for session in sessions:
            session.is_active = False
        
        db.commit()
        
        return True
    
    @staticmethod
    def delete_user(db: Session, user_id: str) -> bool:
        """Delete user account (soft delete)"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Soft delete - mark as inactive
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        # Revoke all sessions and tokens
        UserService.revoke_all_sessions(db, user_id)
        TokenManager.revoke_all_user_tokens(db, user_id)
        
        db.commit()
        
        return True
    
    @staticmethod
    def upgrade_to_premium(db: Session, user_id: str) -> User:
        """Upgrade user to premium subscription"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_premium = True
        user.subscription_tier = 'premium'
        user.subscription_status = 'active'
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def downgrade_to_basic(db: Session, user_id: str) -> User:
        """Downgrade user to basic subscription"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_premium = False
        user.subscription_tier = 'basic'
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def get_user_stats(db: Session, user_id: str) -> Dict[str, Any]:
        """Get user statistics"""
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Count active sessions
        active_sessions = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).count()
        
        # Count refresh tokens
        refresh_tokens = db.query(RefreshToken).filter(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            )
        ).count()
        
        # Calculate account age
        account_age = datetime.utcnow() - user.created_at
        
        return {
            "user_id": user_id,
            "account_age_days": account_age.days,
            "active_sessions": active_sessions,
            "refresh_tokens": refresh_tokens,
            "is_verified": user.is_verified,
            "is_premium": user.is_premium,
            "subscription_tier": user.subscription_tier,
            "last_login": user.last_login,
            "last_activity": user.last_activity
        }

