"""
User Service Database Models
Comprehensive user management with authentication, profiles, and preferences
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    """Core user account information"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    
    # Profile information
    avatar_url = Column(String(500))
    bio = Column(Text)
    current_title = Column(String(255))
    experience_years = Column(Integer, default=0)
    education_level = Column(String(100))
    current_role_level = Column(String(50))  # entry/mid/senior/executive
    
    # Contact information
    phone = Column(String(20))
    location = Column(String(255))
    timezone = Column(String(50))
    
    # Preferences
    preferred_salary_min = Column(Integer)
    preferred_salary_max = Column(Integer)
    preferred_locations = Column(JSON)  # Array of location strings
    preferred_remote_option = Column(Boolean, default=True)
    preferred_company_sizes = Column(JSON)  # Array of company size preferences
    preferred_industries = Column(JSON)  # Array of industry preferences
    
    # Account management
    subscription_tier = Column(String(50), default='basic')  # basic/premium/enterprise
    subscription_status = Column(String(50), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    last_activity = Column(DateTime)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")
    email_verifications = relationship("EmailVerification", back_populates="user", cascade="all, delete-orphan")

class UserProfile(Base):
    """Extended user profile information"""
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, unique=True)
    
    # Professional information
    linkedin_url = Column(String(500))
    github_url = Column(String(500))
    portfolio_url = Column(String(500))
    website_url = Column(String(500))
    
    # Skills and expertise
    skills = Column(JSON)  # Array of skill objects with level
    certifications = Column(JSON)  # Array of certification objects
    languages = Column(JSON)  # Array of language objects with proficiency
    
    # Work preferences
    work_style = Column(String(50))  # remote, hybrid, on-site
    availability = Column(String(50))  # immediate, 2weeks, 1month, 3months
    relocation_willing = Column(Boolean, default=False)
    travel_willing = Column(Boolean, default=False)
    
    # Personal information
    date_of_birth = Column(DateTime)
    gender = Column(String(20))
    nationality = Column(String(100))
    work_authorization = Column(String(100))
    
    # Privacy settings
    profile_visibility = Column(String(20), default='public')  # public, private, connections
    contact_visibility = Column(String(20), default='connections')  # public, connections, private
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profile")

class UserPreference(Base):
    """Detailed user preferences for job matching and notifications"""
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, unique=True)
    
    # Job search preferences
    target_titles = Column(JSON)  # Array of desired job titles
    blacklist_titles = Column(JSON)  # Array of titles to avoid
    target_companies = Column(JSON)  # Array of companies of interest
    blacklist_companies = Column(JSON)  # Array of companies to avoid
    
    # Location preferences
    preferred_locations = Column(JSON)  # Array of location strings
    max_commute_minutes = Column(Integer)
    remote_preference = Column(String(20))  # required, preferred, acceptable, never
    relocation_willing = Column(Boolean, default=False)
    
    # Compensation preferences
    salary_expectation_min = Column(Integer)
    salary_expectation_max = Column(Integer)
    equity_interest = Column(Boolean, default=False)
    benefits_priorities = Column(JSON)  # Array of important benefits
    
    # Work environment preferences
    company_size_preference = Column(JSON)  # startup, small, medium, large, enterprise
    industry_preferences = Column(JSON)  # Array of preferred industries
    culture_priorities = Column(JSON)  # Array of culture attributes
    work_life_balance_importance = Column(Integer)  # 1-5 scale
    
    # Career goals
    career_stage = Column(String(50))  # exploring, advancing, transitioning, executive
    skills_to_develop = Column(JSON)  # Skills user wants to learn
    career_timeline = Column(String(50))  # immediate, 3months, 6months, 1year
    growth_direction = Column(String(100))  # technical, management, consulting, etc
    
    # Job search behavior
    application_frequency = Column(String(20))  # daily, weekly, passive
    auto_apply_enabled = Column(Boolean, default=False)
    notification_preferences = Column(JSON)  # Email, SMS, push preferences
    
    # AI personalization
    matching_algorithm_weights = Column(JSON)  # Custom weights for match factors
    feedback_learning_enabled = Column(Boolean, default=True)
    privacy_level = Column(String(20), default='standard')  # minimal, standard, full
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="preferences")

class UserSession(Base):
    """Track user sessions for security and analytics"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    session_token = Column(String(500), unique=True, nullable=False, index=True)
    
    # Session information
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    device_type = Column(String(50))  # mobile, tablet, desktop
    browser = Column(String(100))
    os = Column(String(100))
    
    # Session status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")

class RefreshToken(Base):
    """JWT refresh tokens for secure authentication"""
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    token = Column(String(500), unique=True, nullable=False, index=True)
    
    # Token information
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime)
    
    # Security information
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

class PasswordReset(Base):
    """Password reset tokens for secure password recovery"""
    __tablename__ = "password_resets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    token = Column(String(500), unique=True, nullable=False, index=True)
    
    # Token information
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime)
    
    # Security information
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="password_resets")

class EmailVerification(Base):
    """Email verification tokens for account verification"""
    __tablename__ = "email_verifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    token = Column(String(500), unique=True, nullable=False, index=True)
    
    # Token information
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="email_verifications")

# Indexes for better performance
Index('idx_users_email', User.email)
Index('idx_users_username', User.username)
Index('idx_users_created_at', User.created_at)
Index('idx_sessions_token', UserSession.session_token)
Index('idx_refresh_tokens_token', RefreshToken.token)
Index('idx_password_resets_token', PasswordReset.token)
Index('idx_email_verifications_token', EmailVerification.token)

