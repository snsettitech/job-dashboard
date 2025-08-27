# Simple Pre-commit setup for Recruitly
param(
    [switch]$Install,
    [switch]$Test
)

Write-Host "🔧 Recruitly Pre-commit Setup" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

if ($Install) {
    Write-Host "`n📦 Installing pre-commit..." -ForegroundColor Yellow

    # Install pre-commit
    try {
        pip install pre-commit
        Write-Host "✅ pre-commit installed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install pre-commit" -ForegroundColor Red
        exit 1
    }

    # Install hooks
    try {
        pre-commit install
        Write-Host "✅ Pre-commit hooks installed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install hooks" -ForegroundColor Red
        exit 1
    }

    Write-Host "`n🎉 Pre-commit setup complete!" -ForegroundColor Green
    Write-Host "Your commits will now automatically run tests and format code." -ForegroundColor Cyan
}

if ($Test) {
    Write-Host "`n🧪 Testing pre-commit hooks..." -ForegroundColor Yellow

    try {
        pre-commit run --all-files
        Write-Host "✅ Pre-commit tests completed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Pre-commit tests failed" -ForegroundColor Red
        exit 1
    }
}

if (-not $Install -and -not $Test) {
    Write-Host "`nUSAGE:" -ForegroundColor Yellow
    Write-Host "  .\scripts\setup-precommit-simple.ps1 -Install    # Install pre-commit hooks" -ForegroundColor White
    Write-Host "  .\scripts\setup-precommit-simple.ps1 -Test       # Test hooks" -ForegroundColor White

    # Show status
    Write-Host "`nSTATUS:" -ForegroundColor Yellow

    # Check if pre-commit is installed
    try {
        $version = pre-commit --version
        Write-Host "✅ pre-commit installed: $version" -ForegroundColor Green
    } catch {
        Write-Host "❌ pre-commit not installed" -ForegroundColor Red
    }

    # Check config file
    if (Test-Path ".pre-commit-config.yaml") {
        Write-Host "✅ Configuration file exists" -ForegroundColor Green
    } else {
        Write-Host "❌ Configuration file missing" -ForegroundColor Red
    }
}
