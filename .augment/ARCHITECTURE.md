# 🏗️ Recruitly Technical Architecture

## System Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   External      │
│   React/TS      │◄──►│   FastAPI       │◄──►│   OpenAI API    │
│   localhost:3000│    │   localhost:8000│    │   GPT-4o-mini   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Static Files  │    │   File Storage  │    │   Embeddings    │
│   Netlify       │    │   Railway       │    │   Vector DB     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Current Implementation Status

### ✅ **Working Components**

#### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── App.tsx                 # Main app with tab navigation
│   ├── components/
│   │   ├── ResumeOptimizer.tsx # Core optimization interface
│   │   ├── Dashboard.tsx       # Analytics dashboard
│   │   ├── JobMatches.tsx      # Job matching interface
│   │   └── Applications.tsx    # Application tracking
│   └── styles/                 # Tailwind CSS styling
```

**Status**: ✅ Fully functional, mobile-responsive, real-time API integration

#### Backend (FastAPI + Python)
```
backend/
├── main.py                     # Entry point (monolithic, needs refactor)
├── app/
│   ├── services/
│   │   ├── enhanced_ai_service.py    # 3-stage optimization pipeline
│   │   ├── ai_service.py             # Core AI with embeddings
│   │   └── enterprise_ats_service.py # ATS compatibility
│   ├── routers/
│   │   └── ai_routes.py              # Modular API routes (not mounted)
│   ├── models/
│   │   └── database.py               # SQLAlchemy models (not integrated)
│   └── utils/
│       └── file_processing.py        # PDF/DOCX/TXT processing
```

**Status**: ✅ Core functionality working, 🔄 Modularization in progress

### 🔄 **In Progress Components**

#### AI Optimization Pipeline
```python
# 3-Stage Pipeline Implementation
Stage 1: Gap Analysis
├── Resume parsing & analysis
├── Job description keyword extraction
├── Skills gap identification
└── ATS compatibility scoring

Stage 2: Strategic Rewriting
├── Content enhancement
├── Keyword optimization
├── Format standardization
└── Executive language upgrade

Stage 3: Quality Validation
├── Overall quality scoring
├── ATS compatibility check
├── Readability assessment
└── Iteration if score < 8.0
```

**Current Issues**:
- ❌ OpenAI API key configuration
- ❌ Numpy compatibility (ComplexWarning import error)
- ❌ Router mounting failure

### 📋 **Planned Components**

#### Database Layer (PostgreSQL)
```sql
-- Core tables for production
users (id, email, created_at, subscription_tier)
optimizations (id, user_id, input_hash, result, feedback, created_at)
job_matches (id, user_id, job_data, match_score, created_at)
learning_patterns (id, pattern_type, data, confidence, created_at)
```

#### Authentication System
```python
# JWT-based authentication
/auth/register    # Email + password registration
/auth/login       # JWT token generation
/auth/refresh     # Token refresh
/auth/logout      # Token invalidation
```

## Data Flow Architecture

### 1. **Resume Optimization Flow**
```
User Upload → File Processing → AI Analysis → 3-Stage Pipeline → Quality Check → User Feedback → Learning Loop
```

### 2. **Job Matching Flow**
```
Resume Embeddings → Job Description Embeddings → Cosine Similarity → Ranking → Match Presentation
```

### 3. **Learning Flow**
```
User Feedback → Pattern Analysis → Prompt Optimization → A/B Testing → Performance Monitoring
```

## Technology Stack

### Frontend
- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React hooks + Context API
- **HTTP Client**: Fetch API with error handling
- **File Upload**: Drag & drop with progress indicators
- **Testing**: Jest + React Testing Library

### Backend
- **Framework**: FastAPI (async/await)
- **Language**: Python 3.12
- **AI Integration**: OpenAI GPT-4o-mini + embeddings
- **File Processing**: PyPDF2, python-docx, python-multipart
- **Vector Operations**: scikit-learn, numpy
- **Testing**: pytest + pytest-asyncio

### Infrastructure
- **Development**: Local (localhost:3000 + localhost:8000)
- **Production**: Netlify (frontend) + Railway (backend)
- **Database**: PostgreSQL (Railway managed)
- **File Storage**: Railway persistent volumes
- **Monitoring**: Railway logs + custom analytics

## Security Architecture

### API Security
```python
# CORS configuration
origins = [
    "http://localhost:3000",
    "https://recruitly.netlify.app"
]

# Rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Implement rate limiting logic
```

### Data Protection
- **API Keys**: Environment variables only
- **User Data**: Encrypted at rest
- **File Processing**: Temporary storage, auto-cleanup
- **Audit Logging**: All optimization requests logged

## Performance Architecture

### Optimization Targets
- **Response Time**: <2 seconds for optimization
- **Throughput**: 100 concurrent optimizations
- **Cost**: <$0.10 per optimization
- **Availability**: 99.9% uptime

### Caching Strategy
```python
# Redis caching for common operations
@cache(expire=3600)
def get_job_embeddings(job_description_hash):
    # Cache job description embeddings

@cache(expire=86400)
def get_industry_patterns(industry):
    # Cache industry-specific optimization patterns
```

## Deployment Architecture

### Development Environment
```bash
# Local development setup
cd backend && python main.py     # Backend on :8000
cd frontend && npm start         # Frontend on :3000
```

### Production Environment
```yaml
# Railway backend deployment
services:
  backend:
    source: backend/
    build:
      commands:
        - pip install -r requirements.txt
    start: python main.py
    env:
      - OPENAI_API_KEY
      - DATABASE_URL

# Netlify frontend deployment
build:
  command: npm run build
  publish: build/
  environment:
    - REACT_APP_API_URL=https://recruitly-backend.railway.app
```

## Monitoring & Analytics

### Application Metrics
- **Optimization Success Rate**: Target >95%
- **Average Processing Time**: Target <10 seconds
- **User Satisfaction**: Target >4.2/5 stars
- **Cost per Optimization**: Target <$0.08

### Technical Metrics
- **API Response Time**: Target <500ms
- **Error Rate**: Target <1%
- **Database Query Time**: Target <100ms
- **Memory Usage**: Target <512MB

## Scalability Plan

### Phase 1: MVP (0-100 users)
- Single Railway instance
- Basic monitoring
- Manual scaling

### Phase 2: Growth (100-1K users)
- Auto-scaling enabled
- Redis caching
- Database optimization

### Phase 3: Scale (1K-10K users)
- Load balancing
- CDN integration
- Microservices architecture

---

**Architecture Version**: 1.0
**Last Updated**: 2025-08-27
**Next Review**: After AI issues resolution
**Status**: Core working, optimization in progress
