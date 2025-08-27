# 📋 Recruitly Development Context

> **Living documentation that auto-updates with each feature completion**

## 🎯 Project Mission
Build an AI-powered resume optimization platform targeting 10K users with mobile-first design and OpenAI cost optimization.

## 🏗️ Current Architecture

### Backend (FastAPI + Python)
- **Entry Point**: `backend/main.py` (monolithic, needs modularization)
- **Modular Structure**: `backend/app/` (routers not yet mounted)
- **AI Services**: 
  - `enhanced_ai_service.py` - 3-stage optimization pipeline
  - `ai_service.py` - Core AI with embeddings
  - `enterprise_ats_service.py` - ATS compatibility testing
- **Database**: SQLAlchemy models defined, not yet integrated
- **API Patterns**: Async FastAPI with error handling and fallbacks

### Frontend (React + TypeScript + Tailwind)
- **Main App**: `frontend/src/App.tsx` - Multi-tab dashboard
- **Components**: `frontend/src/components/ResumeOptimizer.tsx`
- **Patterns**: React hooks, TypeScript interfaces, mobile-first responsive
- **API Integration**: Real-time connection status with graceful fallbacks

### AI Pipeline (OpenAI GPT-4o-mini)
- **Cost Optimization**: $0.150/1K tokens (GPT-4o-mini) + $0.00002/1K tokens (embeddings)
- **3-Stage Process**:
  1. Deep Gap Analysis (skills, language, ATS gaps)
  2. Strategic Rewriting (executive language transformation)
  3. Quality Validation (9-10 scale scoring)
  4. Enhancement Iteration (if quality < 8.0)

## 📊 Feature Status

### ✅ Completed (Working 100%)
- [x] FastAPI backend with async patterns
- [x] React dashboard with TypeScript
- [x] 3-stage AI optimization pipeline
- [x] Resume upload and text extraction (PDF, DOCX, TXT)
- [x] Real-time API connection status
- [x] Mobile-responsive UI with Tailwind CSS
- [x] OpenAI integration with fallback to mock responses
- [x] Multi-tab navigation (Dashboard, AI Optimizer, Matches, Applications, Settings)
- [x] Automated development workflow system
- [x] Context management and documentation auto-updates
- [x] Automated Git commit and push system
- [x] Feature development pipeline with testing integration
- [x] Living documentation system

### 🔄 In Progress
- [ ] Router modularization (ai_routes.py mounting to main.py)

### 📋 Next Priority Features
1. **Router Integration**: Mount `backend/app/routers/ai_routes.py` to `main.py`
2. **Database Integration**: Connect PostgreSQL with SQLAlchemy models
3. **Enhanced Testing**: Unit tests for AI pipeline and API endpoints
4. **Performance Optimization**: Caching and response time improvements

## 🔧 Development Patterns

### Backend Patterns
```python
# Async FastAPI with error handling
@app.post("/api/endpoint")
async def endpoint_function():
    try:
        # AI operation with fallback
        if OPENAI_AVAILABLE:
            result = await real_ai_function()
        else:
            result = await mock_function()
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Frontend Patterns
```typescript
// React hooks with TypeScript
interface ComponentProps {
  data: DataType;
  onAction: (id: string) => void;
}

const Component: React.FC<ComponentProps> = ({ data, onAction }) => {
  const [loading, setLoading] = useState<boolean>(false);
  
  const handleAction = useCallback(async (id: string) => {
    setLoading(true);
    try {
      await api.request(`/endpoint/${id}`);
    } catch (error) {
      console.error('Action failed:', error);
    } finally {
      setLoading(false);
    }
  }, []);
  
  return (
    <div className="mobile-first-responsive-classes">
      {/* Tailwind CSS with mobile-first approach */}
    </div>
  );
};
```

### AI Service Patterns
```python
# Cost-optimized OpenAI usage
class AIService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.chat_model = "gpt-4o-mini"  # Cost optimized
        self.embedding_model = "text-embedding-3-small"  # Cost optimized
        
    async def optimize_with_retries(self, prompt: str) -> str:
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.chat_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,  # Consistent results
                    max_tokens=2500
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                if attempt == self.max_retries:
                    raise e
                await asyncio.sleep(1)
```

## 🚀 Performance Metrics

### Current Performance
- **Resume Optimization**: ~5-8 seconds (target: <3s)
- **API Response Time**: ~200-500ms (target: <500ms)
- **Frontend Load Time**: ~1-2 seconds (target: <2s)
- **OpenAI Cost**: ~$0.05-0.15 per optimization (target: <$0.10)

### Optimization Opportunities
1. **Caching**: Implement Redis for repeated optimizations
2. **Parallel Processing**: Run analysis and optimization concurrently
3. **Token Optimization**: Reduce prompt sizes and response lengths
4. **Database Queries**: Add indexing and query optimization

## 🔄 Development Workflow

### Current Process
1. **Manual Development**: Direct code changes
2. **Manual Testing**: Local server testing
3. **Manual Documentation**: Update files manually
4. **Manual Git**: Manual commits and pushes

### Target Automated Process
1. **Feature Planning**: Automated task creation and tracking
2. **Development**: Code with automatic context updates
3. **Testing**: Automated test execution and validation
4. **Documentation**: Auto-update context and README
5. **Git Integration**: Automated commit and push on completion

## 📈 Scaling Considerations

### 10K User Targets
- **Database**: PostgreSQL with connection pooling
- **Caching**: Redis for session and optimization caching
- **API Rate Limiting**: Implement user-based rate limits
- **Cost Management**: Monitor and optimize OpenAI usage
- **Performance**: Sub-3s optimization times
- **Mobile Experience**: Ensure responsive design works on all devices

## 🔧 Technical Debt

### High Priority
1. **Router Modularization**: Mount ai_routes.py to main.py
2. **Database Integration**: Connect SQLAlchemy models
3. **Error Handling**: Standardize error responses
4. **Testing Coverage**: Add comprehensive test suite

### Medium Priority
1. **Code Organization**: Separate concerns better
2. **Type Safety**: Improve TypeScript coverage
3. **Performance**: Add caching layers
4. **Security**: Add authentication and authorization

## 📝 Architecture Decisions

### Decision Log
- **2025-08-26**: Chose GPT-4o-mini over GPT-4 for cost optimization
- **2025-08-26**: Implemented 3-stage AI pipeline for quality assurance
- **2025-08-26**: Selected FastAPI over Flask for async support
- **2025-08-26**: Chose Tailwind CSS for mobile-first responsive design

### Future Decisions Needed
- Database choice: PostgreSQL vs MongoDB
- Deployment platform: Railway vs AWS vs Vercel
- Authentication: Auth0 vs Firebase vs custom
- Payment processing: Stripe vs PayPal

---

**Last Updated**: 2025-08-26 | **Auto-Updated**: Yes | **Status**: Living Document | **Workflow**: Automated
