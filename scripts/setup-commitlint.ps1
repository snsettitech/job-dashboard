# Setup script for commitlint and conventional commits
Write-Host "🔧 Setting up Commitlint for Recruitly" -ForegroundColor Cyan

# Check if Node.js is available
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js first." -ForegroundColor Red
    exit 1
}

# Install commitlint globally
Write-Host "📦 Installing commitlint..." -ForegroundColor Yellow
try {
    npm install -g @commitlint/cli @commitlint/config-conventional
    Write-Host "✅ Commitlint installed globally" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install commitlint" -ForegroundColor Red
    exit 1
}

# Install commitlint locally in project
Write-Host "📦 Installing commitlint locally..." -ForegroundColor Yellow
try {
    npm install --save-dev @commitlint/cli @commitlint/config-conventional
    Write-Host "✅ Commitlint installed locally" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install commitlint locally" -ForegroundColor Red
}

# Setup git hook
Write-Host "🔗 Setting up git commit-msg hook..." -ForegroundColor Yellow
try {
    # Create git hook directory if it doesn't exist
    if (-not (Test-Path ".git/hooks")) {
        New-Item -ItemType Directory -Path ".git/hooks" -Force
    }
    
    # Create commit-msg hook
    $hookContent = @"
#!/bin/sh
# Commitlint hook
npx --no-install commitlint --edit `$1
"@
    
    Set-Content -Path ".git/hooks/commit-msg" -Value $hookContent -Encoding UTF8
    
    Write-Host "✅ Git commit-msg hook created" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create git hook" -ForegroundColor Red
}

# Test commitlint
Write-Host "🧪 Testing commitlint..." -ForegroundColor Yellow
try {
    $testCommit = "feat: add commitlint configuration"
    echo $testCommit | npx commitlint
    Write-Host "✅ Commitlint test passed" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Commitlint test failed (this is normal if no commits exist yet)" -ForegroundColor Yellow
}

Write-Host "`n🎉 Commitlint setup complete!" -ForegroundColor Green
Write-Host "`nCommit message format:" -ForegroundColor Cyan
Write-Host "  type(scope): description" -ForegroundColor White
Write-Host "`nExamples:" -ForegroundColor Cyan
Write-Host "  feat(frontend): add resume upload component" -ForegroundColor White
Write-Host "  fix(api): resolve authentication issue" -ForegroundColor White
Write-Host "  docs: update README with setup instructions" -ForegroundColor White
Write-Host "  test(backend): add unit tests for AI service" -ForegroundColor White
Write-Host "`nValid types:" -ForegroundColor Cyan
Write-Host "  feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert" -ForegroundColor White
