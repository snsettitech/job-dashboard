# backend/app/models/database_models.py
"""
Database models for job matching and user tracking system
Supports multi-user job matching with persistent data storage
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    """User account and profile information"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Profile information
    current_title = Column(String(255))
    experience_years = Column(Integer, default=0)
    education_level = Column(String(100))
    current_role_level = Column(String(50))  # entry/mid/senior/executive
    
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
    
    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    job_applications = relationship("JobApplication", back_populates="user")
    user_preferences = relationship("UserPreference", back_populates="user", uselist=False)
    match_history = relationship("JobMatchHistory", back_populates="user")

class Resume(Base):
    """User resume versions and content"""
    __tablename__ = "resumes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Resume content
    filename = Column(String(255), nullable=False)
    original_content = Column(Text, nullable=False)
    optimized_content = Column(Text)
    file_type = Column(String(10))  # pdf, docx, txt
    
    # Version control
    version_number = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    # AI analysis results
    extracted_skills = Column(JSON)  # Array of skills found
    experience_summary = Column(JSON)  # Structured experience data
    education_summary = Column(JSON)  # Education information
    achievements = Column(JSON)  # Quantified achievements
    
    # Optimization results
    ats_score_before = Column(Float)
    ats_score_after = Column(Float)
    optimization_improvements = Column(JSON)  # Detailed improvements made
    industry_optimized_for = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="resumes")
    job_matches = relationship("JobMatch", back_populates="resume")

class JobPosting(Base):
    """Job postings from various sources"""
    __tablename__ = "job_postings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_job_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Basic job information
    title = Column(String(500), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), index=True)
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    job_type = Column(String(50))  # full-time, part-time, contract, internship
    remote_option = Column(Boolean, default=False)
    
    # Job content
    description = Column(Text, nullable=False)
    requirements = Column(Text)
    benefits = Column(Text)
    company_description = Column(Text)
    
    # Extracted structured data
    required_skills = Column(JSON)  # Array of required skills
    preferred_skills = Column(JSON)  # Array of preferred skills
    experience_years_min = Column(Integer)
    experience_years_max = Column(Integer)
    education_requirements = Column(JSON)
    role_level = Column(String(50))  # entry/mid/senior/executive
    industry = Column(String(100), index=True)
    company_size = Column(String(50))
    
    # Source information
    source = Column(String(100), nullable=False)  # indeed, linkedin, company_site
    source_url = Column(String(1000))
    application_url = Column(String(1000))
    posted_date = Column(DateTime, index=True)
    expires_date = Column(DateTime)
    
    # Status tracking
    is_active = Column(Boolean, default=True, index=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job_matches = relationship("JobMatch", back_populates="job_posting")
    applications = relationship("JobApplication", back_populates="job_posting")

class JobMatch(Base):
    """Individual job matches with scoring details"""
    __tablename__ = "job_matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    resume_id = Column(UUID(as_uuid=True), ForeignKey('resumes.id'), nullable=False)
    job_posting_id = Column(UUID(as_uuid=True), ForeignKey('job_postings.id'), nullable=False)
    
    # Match scoring
    composite_score = Column(Float, nullable=False, index=True)
    skills_alignment_score = Column(Float, nullable=False)
    experience_relevance_score = Column(Float, nullable=False) 
    role_progression_score = Column(Float, nullable=False)
    company_culture_score = Column(Float, nullable=False)
    confidence_level = Column(String(20))  # High/Medium/Low
    
    # Match analysis
    matching_skills = Column(JSON)  # Skills that match
    missing_skills = Column(JSON)  # Skills user needs to develop
    match_reasons = Column(JSON)  # Human-readable reasons for match
    improvement_suggestions = Column(JSON)  # Ways to improve match score
    
    # User interaction
    user_interest_level = Column(Integer)  # 1-5 rating from user
    user_notes = Column(Text)
    is_bookmarked = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=False)
    viewed_at = Column(DateTime)
    
    # Status
    match_status = Column(String(50), default='new')  # new/viewed/interested/applied/rejected
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    resume = relationship("Resume", back_populates="job_matches")
    job_posting = relationship("JobPosting", back_populates="job_matches")

class JobApplication(Base):
    """Track job applications and their status"""
    __tablename__ = "job_applications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    job_posting_id = Column(UUID(as_uuid=True), ForeignKey('job_postings.id'), nullable=False)
    resume_id = Column(UUID(as_uuid=True), ForeignKey('resumes.id'), nullable=False)
    
    # Application details
    application_method = Column(String(50))  # manual, auto_apply, email
    cover_letter_content = Column(Text)
    custom_resume_used = Column(Boolean, default=False)
    
    # Status tracking
    application_status = Column(String(50), default='submitted')  
    # submitted, under_review, phone_screen, interview_scheduled, 
    # interviewed, offer_received, accepted, rejected, withdrawn
    
    # Timeline
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_status_update = Column(DateTime, default=datetime.utcnow)
    response_received_at = Column(DateTime)
    interview_scheduled_at = Column(DateTime)
    interview_completed_at = Column(DateTime)
    offer_received_at = Column(DateTime)
    final_decision_at = Column(DateTime)
    
    # Communication tracking
    recruiter_contact = Column(String(255))
    hiring_manager_contact = Column(String(255))
    communication_log = Column(JSON)  # Array of communication events
    
    # Follow-up automation
    auto_followup_enabled = Column(Boolean, default=True)
    next_followup_date = Column(DateTime)
    followup_count = Column(Integer, default=0)
    
    # Application insights
    estimated_callback_probability = Column(Float)  # AI prediction 0-1
    application_quality_score = Column(Float)  # How well application matches job
    competition_level = Column(String(20))  # High/Medium/Low based on job popularity
    
    # Results tracking
    got_callback = Column(Boolean)
    callback_days = Column(Integer)  # Days between application and callback
    rejection_reason = Column(String(500))
    offer_amount = Column(Integer)
    negotiated_amount = Column(Integer)
    
    # Relationships
    user = relationship("User", back_populates="job_applications")
    job_posting = relationship("JobPosting", back_populates="applications")

class UserPreference(Base):
    """Detailed user preferences for job matching"""
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
    user = relationship("User", back_populates="user_preferences")

class JobMatchHistory(Base):
    """Track historical matching performance for ML improvement"""
    __tablename__ = "job_match_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    job_posting_id = Column(UUID(as_uuid=True), ForeignKey('job_postings.id'), nullable=False)
    
    # Prediction vs Reality tracking
    predicted_match_score = Column(Float, nullable=False)
    predicted_callback_probability = Column(Float)
    predicted_interest_level = Column(Float)
    
    # Actual outcomes
    user_showed_interest = Column(Boolean)  # Did user apply or bookmark?
    user_interest_rating = Column(Integer)  # 1-5 if user provided feedback
    did_apply = Column(Boolean, default=False)
    got_callback = Column(Boolean)
    got_interview = Column(Boolean)
    got_offer = Column(Boolean)
    accepted_offer = Column(Boolean)
    
    # Learning data
    match_accuracy_score = Column(Float)  # How accurate was our prediction?
    factors_that_mattered = Column(JSON)  # What the user actually cared about
    user_feedback = Column(Text)  # Optional user feedback on match quality
    
    # Model improvement data
    algorithm_version = Column(String(50))  # Track which version made prediction
    model_confidence = Column(Float)  # How confident was the model?
    feature_importance = Column(JSON)  # Which features drove the prediction
    
    # Timestamps
    predicted_at = Column(DateTime, default=datetime.utcnow)
    outcome_recorded_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="match_history")

class CompanyProfile(Base):
    """Company information for better matching"""
    __tablename__ = "company_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(255), unique=True, nullable=False, index=True)
    
    # Basic company info
    industry = Column(String(100), index=True)
    company_size = Column(String(50))  # startup, small, medium, large, enterprise
    founded_year = Column(Integer)
    headquarters_location = Column(String(255))
    website = Column(String(500))
    linkedin_url = Column(String(500))
    
    # Company culture data
    glassdoor_rating = Column(Float)
    culture_keywords = Column(JSON)  # Extracted from reviews
    benefits_offered = Column(JSON)  # Array of benefits
    remote_policy = Column(String(50))  # remote-first, hybrid, office-required
    work_life_balance_rating = Column(Float)
    diversity_rating = Column(Float)
    
    # Hiring patterns
    avg_hiring_time = Column(Integer)  # Days from application to offer
    callback_rate = Column(Float)  # Historical callback rate
    common_interview_process = Column(JSON)  # Typical interview stages
    salary_competitiveness = Column(String(20))  # below-market, competitive, above-market
    
    # AI insights
    hiring_preferences = Column(JSON)  # What they typically look for
    red_flags = Column(JSON)  # Warning signs from employee reviews
    growth_trajectory = Column(String(50))  # growing, stable, declining
    
    # Data freshness
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_sources = Column(JSON)  # Where we got this data

class SkillTrend(Base):
    """Track skill demand trends for market intelligence"""
    __tablename__ = "skill_trends"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_name = Column(String(100), nullable=False, index=True)
    industry = Column(String(100), index=True)
    role_level = Column(String(50), index=True)
    
    # Trend data
    demand_score = Column(Float)  # 0-100 relative demand
    growth_rate = Column(Float)  # % change over time
    salary_premium = Column(Float)  # Average salary boost for this skill
    
    # Market data
    job_postings_count = Column(Integer)  # Number of jobs mentioning this skill
    avg_salary_with_skill = Column(Integer)
    avg_salary_without_skill = Column(Integer)
    competition_level = Column(String(20))  # high, medium, low
    
    # Learning recommendations
    learning_difficulty = Column(String(20))  # easy, medium, hard
    estimated_learning_time_months = Column(Integer)
    top_learning_resources = Column(JSON)  # URLs and resource names
    related_skills = Column(JSON)  # Skills often found together
    
    # Time tracking
    data_period_start = Column(DateTime)
    data_period_end = Column(DateTime)
    calculated_at = Column(DateTime, default=datetime.utcnow)

# Database utility functions
class DatabaseManager:
    """Utility class for database operations"""
    
    @staticmethod
    def create_all_tables(engine):
        """Create all tables in the database"""
        Base.metadata.create_all(bind=engine)
    
    @staticmethod
    def drop_all_tables(engine):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(bind=engine)
    
    @staticmethod
    def get_table_names():
        """Get list of all table names"""
        return [table.name for table in Base.metadata.tables.values()]

# Sample data creation functions for testing
def create_sample_user(session, email: str = "test@example.com") -> User:
    """Create a sample user for testing"""
    user = User(
        email=email,
        full_name="John Doe",
        password_hash="hashed_password_here",
        current_title="Senior Software Engineer",
        experience_years=5,
        education_level="Bachelor's Degree",
        current_role_level="senior",
        preferred_salary_min=120000,
        preferred_salary_max=180000,
        preferred_locations=["San Francisco", "Remote", "New York"],
        preferred_remote_option=True,
        preferred_company_sizes=["medium", "large"],
        preferred_industries=["technology", "fintech"],
        subscription_tier="premium"
    )
    session.add(user)
    session.commit()
    return user

def create_sample_job_posting(session, title: str = "Senior Python Developer") -> JobPosting:
    """Create a sample job posting for testing"""
    job = JobPosting(
        external_job_id=f"job_{uuid.uuid4().hex[:8]}",
        title=title,
        company="TechCorp Inc",
        location="San Francisco, CA",
        salary_min=130000,
        salary_max=170000,
        job_type="full-time",
        remote_option=True,
        description="""
        We are seeking a Senior Python Developer to join our growing team.
        You will work on scalable web applications and data processing systems.
        
        Requirements:
        - 4+ years of Python development experience
        - Experience with Django/Flask frameworks
        - Knowledge of cloud platforms (AWS, GCP)
        - Strong problem-solving skills
        
        Nice to have:
        - React/JavaScript experience
        - Docker and Kubernetes knowledge
        - Machine learning background
        """,
        required_skills=["python", "django", "aws", "postgresql"],
        preferred_skills=["react", "docker", "kubernetes", "machine learning"],
        experience_years_min=4,
        experience_years_max=8,
        role_level="senior",
        industry="technology",
        company_size="medium",
        source="indeed",
        source_url="https://indeed.com/job/12345",
        application_url="https://techcorp.com/apply/12345",
        posted_date=datetime.utcnow(),
        is_active=True
    )
    session.add(job)
    session.commit()
    return job

# Export all models and utilities
__all__ = [
    'Base',
    'User', 
    'Resume',
    'JobPosting',
    'JobMatch', 
    'JobApplication',
    'UserPreference',
    'JobMatchHistory',
    'CompanyProfile',
    'SkillTrend',
    'DatabaseManager',
    'create_sample_user',
    'create_sample_job_posting'
]