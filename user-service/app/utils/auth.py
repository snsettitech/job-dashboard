"""
JWT Authentication Utilities
Handles token creation, validation, and user authentication
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..models.user_models import User
from ..models.schemas import UserResponse

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
SESSION_TOKEN_EXPIRE_DAYS = int(os.getenv("SESSION_TOKEN_EXPIRE_DAYS", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()

class AuthService:
    """Authentication service for JWT token management"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_session_token(data: Dict[str, Any]) -> str:
        """Create session token for tracking user sessions"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=SESSION_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "session"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            token_type_from_payload = payload.get("type")
            
            if token_type_from_payload != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}, got {token_type_from_payload}"
                )
            
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not AuthService.verify_password(password, user.password_hash):
            return None
        return user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def update_last_login(db: Session, user: User) -> None:
        """Update user's last login timestamp"""
        user.last_login = datetime.utcnow()
        user.last_activity = datetime.utcnow()
        db.commit()
    
    @staticmethod
    def update_last_activity(db: Session, user: User) -> None:
        """Update user's last activity timestamp"""
        user.last_activity = datetime.utcnow()
        db.commit()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = AuthService.verify_token(token, "access")
    user_id: str = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    user = AuthService.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def get_current_verified_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current verified user"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user

def get_current_premium_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current premium user"""
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required"
        )
    return current_user

# Database dependency (to be imported from database module)
def get_db():
    """Database dependency - to be implemented in database module"""
    from ..database import get_db
    return get_db()

class TokenManager:
    """Token management for refresh tokens and sessions"""
    
    @staticmethod
    def create_refresh_token_record(db: Session, user_id: str, token: str, ip_address: str = None, user_agent: str = None):
        """Create refresh token record in database"""
        from ..models.user_models import RefreshToken
        
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(refresh_token)
        db.commit()
        return refresh_token
    
    @staticmethod
    def create_session_record(db: Session, user_id: str, session_token: str, ip_address: str = None, user_agent: str = None):
        """Create session record in database"""
        from ..models.user_models import UserSession
        
        expires_at = datetime.utcnow() + timedelta(days=SESSION_TOKEN_EXPIRE_DAYS)
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(session)
        db.commit()
        return session
    
    @staticmethod
    def revoke_refresh_token(db: Session, token: str):
        """Revoke refresh token"""
        from ..models.user_models import RefreshToken
        
        refresh_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
        if refresh_token:
            refresh_token.is_revoked = True
            refresh_token.revoked_at = datetime.utcnow()
            db.commit()
    
    @staticmethod
    def revoke_all_user_tokens(db: Session, user_id: str):
        """Revoke all refresh tokens for a user"""
        from ..models.user_models import RefreshToken
        
        refresh_tokens = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).all()
        
        for token in refresh_tokens:
            token.is_revoked = True
            token.revoked_at = datetime.utcnow()
        
        db.commit()
    
    @staticmethod
    def cleanup_expired_tokens(db: Session):
        """Clean up expired tokens"""
        from ..models.user_models import RefreshToken, UserSession
        
        # Clean up expired refresh tokens
        expired_refresh_tokens = db.query(RefreshToken).filter(
            RefreshToken.expires_at < datetime.utcnow()
        ).all()
        
        for token in expired_refresh_tokens:
            db.delete(token)
        
        # Clean up expired sessions
        expired_sessions = db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        ).all()
        
        for session in expired_sessions:
            db.delete(session)
        
        db.commit()

class PasswordManager:
    """Password management utilities"""
    
    @staticmethod
    def create_password_reset_token(db: Session, user_id: str, token: str, ip_address: str = None, user_agent: str = None):
        """Create password reset token"""
        from ..models.user_models import PasswordReset
        
        expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
        password_reset = PasswordReset(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(password_reset)
        db.commit()
        return password_reset
    
    @staticmethod
    def verify_password_reset_token(db: Session, token: str):
        """Verify password reset token"""
        from ..models.user_models import PasswordReset
        
        password_reset = db.query(PasswordReset).filter(
            PasswordReset.token == token,
            PasswordReset.is_used == False,
            PasswordReset.expires_at > datetime.utcnow()
        ).first()
        
        return password_reset
    
    @staticmethod
    def mark_password_reset_used(db: Session, token: str):
        """Mark password reset token as used"""
        from ..models.user_models import PasswordReset
        
        password_reset = db.query(PasswordReset).filter(PasswordReset.token == token).first()
        if password_reset:
            password_reset.is_used = True
            password_reset.used_at = datetime.utcnow()
            db.commit()

class EmailVerificationManager:
    """Email verification utilities"""
    
    @staticmethod
    def create_verification_token(db: Session, user_id: str, token: str):
        """Create email verification token"""
        from ..models.user_models import EmailVerification
        
        expires_at = datetime.utcnow() + timedelta(hours=72)  # 72 hour expiry
        verification = EmailVerification(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.add(verification)
        db.commit()
        return verification
    
    @staticmethod
    def verify_email_token(db: Session, token: str):
        """Verify email verification token"""
        from ..models.user_models import EmailVerification
        
        verification = db.query(EmailVerification).filter(
            EmailVerification.token == token,
            EmailVerification.is_used == False,
            EmailVerification.expires_at > datetime.utcnow()
        ).first()
        
        return verification
    
    @staticmethod
    def mark_verification_used(db: Session, token: str):
        """Mark email verification token as used"""
        from ..models.user_models import EmailVerification
        
        verification = db.query(EmailVerification).filter(EmailVerification.token == token).first()
        if verification:
            verification.is_used = True
            verification.used_at = datetime.utcnow()
            db.commit()

