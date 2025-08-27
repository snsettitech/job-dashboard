# Recruitly Core Context - Master Reference

## 🎯 PROJECT IDENTITY
- **Name**: Recruitly
- **Purpose**: AI-powered resume optimization for 25%+ callback rate improvement
- **Target**: 10,000 active users, $50K+ MRR
- **Current Phase**: 1C (Production Deployment + Beta Testing)
## 🤖 AI OPTIMIZATION PIPELINE
### Stage 1: Analysis Engine
- Input: Resume text + job description
- Process: ATS scoring, keyword gap analysis, weakness detection
- Output: Detailed improvement areas with scoring (1-100)

### Stage 2: Transformation Engine  
- Input: Analysis results + optimization strategies
- Process: Language enhancement, keyword integration, impact quantification
- Output: Optimized resume with strategic improvements

### Stage 3: Validation Engine
- Input: Original vs optimized resume comparison
- Process: Quality scoring, improvement measurement, ATS re-evaluation
- Output: Before/after metrics with confidence scores

## 💰 BUSINESS METRICS
- **Cost per optimization**: $0.02-0.05 (OpenAI tokens)
- **Target processing time**: <30 seconds
- **Quality threshold**: >80% ATS improvement
- **User satisfaction target**: >8/10

## 🚀 DEPLOYMENT PIPELINE
- **Development**: Local (localhost:3000 + localhost:8000)
- **Frontend Production**: Netlify (React build)
- **Backend Production**: Railway (FastAPI server)
- **Database**: PostgreSQL (planned)
- **Repository**: https://github.com/snsettitech/job-dashboard

## 🎯 CODING STANDARDS
### React/TypeScript Frontend
- Functional components with React hooks
- TypeScript interfaces for all props and data
- Tailwind CSS utilities (NO custom CSS)
- Mobile-first responsive design (60% mobile users)
- Lucide React icons only
- Error boundaries around AI operations

### FastAPI Backend  
- Async/await for all endpoints
- Pydantic models for request/response validation
- Dependency injection pattern
- Structured JSON error responses
- CORS configuration for frontend integration
- Environment variable configuration

### AI Integration Patterns
- OpenAI client initialization in enhanced_ai_service.py
- Token usage monitoring and cost tracking
- Rate limiting and retry logic
- Error handling with user-friendly messages
- File processing: PDF (PyMuPDF), DOCX (python-docx), TXT (direct)

## ⚠️ CRITICAL CONSTRAINTS
- **Resume Optimization Performance**: 60% users want resume optimization accurately within 30 seconds
- **Cost Optimization**: OpenAI token efficiency crucial
- **ATS Compatibility**: Resume must parse correctly in ATS systems
- **User Experience**: Smooth, intuitive interface required
- **Scalability**: Architecture must handle 10K+ concurrent users
- **Production Reliability**: Zero downtime deployment requirement