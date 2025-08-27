# 🔄 Recruitly Development Workflow Guide

> **Complete guide to using the automated development workflow system**

## 🎯 Overview

The Recruitly project now features a **fully automated development workflow** that:
- ✅ Tracks feature development progress
- ✅ Updates documentation automatically
- ✅ Runs comprehensive tests before commits
- ✅ Commits and pushes to GitHub when features are 100% complete
- ✅ Maintains living project context

## 🚀 Quick Start

### 1. Check System Status
```powershell
.\scripts\dev.ps1 status
```
This shows:
- Git repository status
- Backend/Frontend server status
- Recent feature development log

### 2. Start a New Feature
```powershell
.\scripts\dev.ps1 start -Feature "router-integration" -Description "Mount ai_routes.py to main.py"
```
This will:
- Create a feature branch
- Initialize feature tracking
- Update the feature log

### 3. Update Feature Progress
```powershell
.\scripts\dev.ps1 update -Feature "router-integration" -Files @("backend/main.py", "backend/app/routers/ai_routes.py") -Notes "Added router mounting logic"
```

### 4. Complete Feature (Auto-Commit)
```powershell
.\scripts\dev.ps1 complete -Feature "router-integration"
```
This will:
- Run full test suite (backend + frontend)
- Update documentation automatically
- Commit changes with conventional commit message
- Push to GitHub
- Update project context

## 📋 Workflow Commands

### PowerShell Commands (Windows)
```powershell
# Check project status
.\scripts\dev.ps1 status

# Start new feature
.\scripts\dev.ps1 start -Feature "feature-name" -Description "Feature description"

# Update feature progress
.\scripts\dev.ps1 update -Feature "feature-name" -Files @("file1.py", "file2.tsx") -Notes "Progress notes"

# Complete feature (runs tests, updates docs, commits)
.\scripts\dev.ps1 complete -Feature "feature-name"

# Manual auto-commit
.\scripts\dev.ps1 commit -Feature "feature-name" -Description "Feature description"

# Run tests only
.\scripts\dev.ps1 test
```

### Python Commands (Cross-platform)
```bash
# Start feature
python scripts/dev-workflow.py start --feature "feature-name" --description "Feature description"

# Update progress
python scripts/dev-workflow.py update --feature "feature-name" --files "file1.py" "file2.tsx" --notes "Progress notes"

# Complete feature
python scripts/dev-workflow.py complete --feature "feature-name" --message "Custom commit message"

# Auto-commit completed feature
python scripts/auto-commit.py "feature-name" "Feature description"
```

## 🧪 Testing Integration

The workflow automatically runs comprehensive tests before any commit:

### Backend Tests
- Python unit tests with pytest
- API endpoint testing
- Service layer validation

### Frontend Tests
- React component tests
- TypeScript compilation
- Build validation

### Integration Tests
- API health checks
- Full stack connectivity
- End-to-end workflow validation

## 📝 Documentation Updates

The system automatically updates:

### 1. Development Context (`docs/DEVELOPMENT_CONTEXT.md`)
- Adds completed features to the ✅ section
- Updates architecture decisions
- Tracks performance metrics
- Records technical debt

### 2. README.md
- Updates "Current Status" section
- Refreshes last updated timestamp
- Maintains feature completion list

### 3. Feature Log (`docs/FEATURE_LOG.json`)
- Tracks all feature development
- Records timestamps and progress
- Maintains development history

### 4. Commit Log (`docs/COMMIT_LOG.json`)
- Logs all automated commits
- Tracks success/failure status
- Maintains commit history

## 🔄 Git Integration

### Automated Git Operations
1. **Feature Branches**: Creates `feature/feature-name` branches
2. **Conventional Commits**: Uses standard commit message format
3. **Auto-Push**: Pushes to GitHub when tests pass
4. **Branch Cleanup**: Removes feature branches after merge

### Commit Message Format
```
feat(scope): description
fix(scope): description
docs(scope): description
test(scope): description
refactor(scope): description
```

Examples:
- `feat(backend): integrate modular router system`
- `fix(frontend): resolve mobile responsive layout issues`
- `docs: update development workflow guide`

## 📊 Project Context Management

### Living Documentation
The system maintains **living documentation** that automatically updates:

- **Architecture Overview**: Current tech stack and patterns
- **Feature Status**: Real-time completion tracking
- **Performance Metrics**: Response times and optimization targets
- **Technical Debt**: Known issues and improvement areas
- **Development Patterns**: Code standards and best practices

### Context Preservation
Every feature completion updates:
- Project architecture understanding
- Development patterns and standards
- Performance benchmarks
- Future planning and roadmap

## 🎯 Best Practices

### 1. Feature Naming
- Use kebab-case: `router-integration`, `database-setup`
- Be descriptive: `ai-optimization-pipeline`, `mobile-responsive-ui`
- Include scope: `backend-router-integration`, `frontend-mobile-layout`

### 2. Feature Descriptions
- Be specific: "Mount ai_routes.py to main.py for modular API structure"
- Include context: "Integrate PostgreSQL with SQLAlchemy models for user data"
- Mention impact: "Optimize OpenAI API calls to reduce cost by 30%"

### 3. Progress Updates
- Update frequently with meaningful notes
- List all files changed
- Include any tests added
- Note any blockers or decisions made

### 4. Feature Completion
- Ensure all tests pass locally first
- Verify both backend and frontend work
- Test the complete user workflow
- Let the system handle documentation and Git operations

## 🚨 Troubleshooting

### Common Issues

#### Tests Failing
```powershell
# Run tests manually to see detailed output
cd backend && python -m pytest -v
cd frontend && npm test -- --watchAll=false
```

#### Backend Not Running
```bash
cd backend
python main.py
# Check http://localhost:8000/health
```

#### Frontend Not Building
```bash
cd frontend
npm install
npm start
# Check http://localhost:3000
```

#### Git Issues
```bash
# Check git status
git status

# Reset if needed
git reset --hard HEAD

# Check remote
git remote -v
```

### Recovery Commands
```powershell
# Reset workflow state
Remove-Item docs\FEATURE_LOG.json
python scripts/dev-workflow.py start --feature "recovery" --description "Reset workflow state"

# Manual commit if auto-commit fails
git add .
git commit -m "manual: recovery commit"
git push origin main
```

## 📈 Performance Monitoring

The workflow tracks:
- **Feature Development Time**: From start to completion
- **Test Execution Time**: Backend and frontend test duration
- **Commit Success Rate**: Automated vs manual commits
- **Documentation Coverage**: Auto-updated vs manual updates

## 🔮 Future Enhancements

Planned workflow improvements:
- [ ] Integration with GitHub Actions for CI/CD
- [ ] Automated deployment on feature completion
- [ ] Performance regression testing
- [ ] Automated dependency updates
- [ ] Code quality metrics integration

---

**Last Updated**: 2025-08-26 | **Version**: 1.0.0 | **Status**: Production Ready
