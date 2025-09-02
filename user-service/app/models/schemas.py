"""
Pydantic schemas for User Service API
Request/response models with validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import re

# Base schemas
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

# Authentication schemas
class UserRegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def validate_password_match(cls, v, values):
        """Validate password confirmation"""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v

class UserLoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False

class UserLoginResponse(BaseResponse):
    """User login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: 'UserResponse'

class TokenRefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str

class TokenRefreshResponse(BaseResponse):
    """Token refresh response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr

class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation request"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def validate_password_match(cls, v, values):
        """Validate password confirmation"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

# User schemas
class UserResponse(BaseModel):
    """User response model"""
    id: UUID
    email: str
    username: Optional[str]
    full_name: str
    is_active: bool
    is_verified: bool
    is_premium: bool
    avatar_url: Optional[str]
    current_title: Optional[str]
    experience_years: Optional[int]
    location: Optional[str]
    subscription_tier: str
    subscription_status: str
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

class UserProfileResponse(BaseModel):
    """User profile response model"""
    id: UUID
    user_id: UUID
    linkedin_url: Optional[str]
    github_url: Optional[str]
    portfolio_url: Optional[str]
    website_url: Optional[str]
    skills: Optional[List[Dict[str, Any]]]
    certifications: Optional[List[Dict[str, Any]]]
    languages: Optional[List[Dict[str, Any]]]
    work_style: Optional[str]
    availability: Optional[str]
    relocation_willing: Optional[bool]
    travel_willing: Optional[bool]
    profile_visibility: str
    contact_visibility: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserPreferenceResponse(BaseModel):
    """User preference response model"""
    id: UUID
    user_id: UUID
    target_titles: Optional[List[str]]
    blacklist_titles: Optional[List[str]]
    target_companies: Optional[List[str]]
    blacklist_companies: Optional[List[str]]
    preferred_locations: Optional[List[str]]
    max_commute_minutes: Optional[int]
    remote_preference: Optional[str]
    relocation_willing: Optional[bool]
    salary_expectation_min: Optional[int]
    salary_expectation_max: Optional[int]
    equity_interest: Optional[bool]
    benefits_priorities: Optional[List[str]]
    company_size_preference: Optional[List[str]]
    industry_preferences: Optional[List[str]]
    culture_priorities: Optional[List[str]]
    work_life_balance_importance: Optional[int]
    career_stage: Optional[str]
    skills_to_develop: Optional[List[str]]
    career_timeline: Optional[str]
    growth_direction: Optional[str]
    application_frequency: Optional[str]
    auto_apply_enabled: Optional[bool]
    notification_preferences: Optional[Dict[str, Any]]
    matching_algorithm_weights: Optional[Dict[str, Any]]
    feedback_learning_enabled: Optional[bool]
    privacy_level: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Profile update schemas
class UserProfileUpdateRequest(BaseModel):
    """User profile update request"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    current_title: Optional[str] = Field(None, max_length=255)
    experience_years: Optional[int] = Field(None, ge=0, le=50)
    education_level: Optional[str] = Field(None, max_length=100)
    current_role_level: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=255)
    timezone: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=1000)
    avatar_url: Optional[str] = Field(None, max_length=500)

class ExtendedProfileUpdateRequest(BaseModel):
    """Extended profile update request"""
    linkedin_url: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)
    portfolio_url: Optional[str] = Field(None, max_length=500)
    website_url: Optional[str] = Field(None, max_length=500)
    skills: Optional[List[Dict[str, Any]]]
    certifications: Optional[List[Dict[str, Any]]]
    languages: Optional[List[Dict[str, Any]]]
    work_style: Optional[str] = Field(None, max_length=50)
    availability: Optional[str] = Field(None, max_length=50)
    relocation_willing: Optional[bool]
    travel_willing: Optional[bool]
    profile_visibility: Optional[str] = Field(None, max_length=20)
    contact_visibility: Optional[str] = Field(None, max_length=20)

class UserPreferenceUpdateRequest(BaseModel):
    """User preference update request"""
    target_titles: Optional[List[str]]
    blacklist_titles: Optional[List[str]]
    target_companies: Optional[List[str]]
    blacklist_companies: Optional[List[str]]
    preferred_locations: Optional[List[str]]
    max_commute_minutes: Optional[int] = Field(None, ge=0, le=300)
    remote_preference: Optional[str] = Field(None, max_length=20)
    relocation_willing: Optional[bool]
    salary_expectation_min: Optional[int] = Field(None, ge=0)
    salary_expectation_max: Optional[int] = Field(None, ge=0)
    equity_interest: Optional[bool]
    benefits_priorities: Optional[List[str]]
    company_size_preference: Optional[List[str]]
    industry_preferences: Optional[List[str]]
    culture_priorities: Optional[List[str]]
    work_life_balance_importance: Optional[int] = Field(None, ge=1, le=5)
    career_stage: Optional[str] = Field(None, max_length=50)
    skills_to_develop: Optional[List[str]]
    career_timeline: Optional[str] = Field(None, max_length=50)
    growth_direction: Optional[str] = Field(None, max_length=100)
    application_frequency: Optional[str] = Field(None, max_length=20)
    auto_apply_enabled: Optional[bool]
    notification_preferences: Optional[Dict[str, Any]]
    matching_algorithm_weights: Optional[Dict[str, Any]]
    feedback_learning_enabled: Optional[bool]
    privacy_level: Optional[str] = Field(None, max_length=20)

# Password change schema
class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def validate_password_match(cls, v, values):
        """Validate password confirmation"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

# Email verification schema
class EmailVerificationRequest(BaseModel):
    """Email verification request"""
    token: str

# Session management schemas
class SessionResponse(BaseModel):
    """Session response model"""
    id: UUID
    user_id: UUID
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_type: Optional[str]
    browser: Optional[str]
    os: Optional[str]
    is_active: bool
    expires_at: datetime
    created_at: datetime
    last_activity: datetime
    
    class Config:
        from_attributes = True

class SessionListResponse(BaseResponse):
    """Session list response"""
    sessions: List[SessionResponse]
    total_count: int

# User list and search schemas
class UserListResponse(BaseResponse):
    """User list response"""
    users: List[UserResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class UserSearchRequest(BaseModel):
    """User search request"""
    query: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"

# Health check schema
class HealthCheckResponse(BaseResponse):
    """Health check response"""
    status: str
    version: str
    database_status: str
    redis_status: Optional[str]
    uptime: float

