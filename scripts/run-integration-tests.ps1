# Integration test runner for Recruitly
param(
    [switch]$StartServices,
    [switch]$StopServices,
    [switch]$TestOnly,
    [string]$TestPattern = "*"
)

function Write-Banner {
    param([string]$Message)
    Write-Host "`n🧪 $Message" -ForegroundColor Cyan
    Write-Host ("=" * ($Message.Length + 4)) -ForegroundColor Cyan
}

function Start-BackendService {
    Write-Host "🚀 Starting backend service..." -ForegroundColor Yellow
    
    Push-Location backend
    try {
        # Check if virtual environment exists
        if (Test-Path "venv/Scripts/activate.ps1") {
            Write-Host "🐍 Activating virtual environment..." -ForegroundColor Yellow
            & venv/Scripts/activate.ps1
        }
        
        # Start backend in background
        Start-Process -FilePath "python" -ArgumentList "main.py" -WindowStyle Hidden -PassThru
        Write-Host "✅ Backend service started" -ForegroundColor Green
        
        # Wait for backend to be ready
        $maxRetries = 30
        for ($i = 0; $i -lt $maxRetries; $i++) {
            try {
                $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 2
                if ($response.status -eq "healthy") {
                    Write-Host "✅ Backend is ready" -ForegroundColor Green
                    break
                }
            } catch {
                Start-Sleep -Seconds 2
            }
            
            if ($i -eq $maxRetries - 1) {
                Write-Host "❌ Backend failed to start" -ForegroundColor Red
                return $false
            }
        }
    } finally {
        Pop-Location
    }
    
    return $true
}

function Start-FrontendService {
    Write-Host "🚀 Starting frontend service..." -ForegroundColor Yellow
    
    Push-Location frontend
    try {
        # Check if node_modules exists
        if (-not (Test-Path "node_modules")) {
            Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
            npm install
        }
        
        # Start frontend in background
        Start-Process -FilePath "npm" -ArgumentList "start" -WindowStyle Hidden -PassThru
        Write-Host "✅ Frontend service started" -ForegroundColor Green
        
        # Wait for frontend to be ready
        $maxRetries = 30
        for ($i = 0; $i -lt $maxRetries; $i++) {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:3000" -Method Get -TimeoutSec 2
                if ($response.StatusCode -eq 200) {
                    Write-Host "✅ Frontend is ready" -ForegroundColor Green
                    break
                }
            } catch {
                Start-Sleep -Seconds 2
            }
            
            if ($i -eq $maxRetries - 1) {
                Write-Host "❌ Frontend failed to start" -ForegroundColor Red
                return $false
            }
        }
    } finally {
        Pop-Location
    }
    
    return $true
}

function Stop-Services {
    Write-Host "🛑 Stopping services..." -ForegroundColor Yellow
    
    # Stop processes running on ports 8000 and 3000
    $processes = Get-NetTCPConnection -LocalPort 8000, 3000 -ErrorAction SilentlyContinue | 
                 Select-Object -ExpandProperty OwningProcess | 
                 Get-Process -Id { $_ } -ErrorAction SilentlyContinue
    
    foreach ($process in $processes) {
        try {
            Stop-Process -Id $process.Id -Force
            Write-Host "✅ Stopped process: $($process.ProcessName)" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ Could not stop process: $($process.ProcessName)" -ForegroundColor Yellow
        }
    }
}

function Run-IntegrationTests {
    Write-Banner "Running Integration Tests"
    
    # Ensure we're in the project root
    if (-not (Test-Path "tests/integration")) {
        Write-Host "❌ Integration tests directory not found" -ForegroundColor Red
        return $false
    }
    
    # Install test dependencies
    Write-Host "📦 Installing test dependencies..." -ForegroundColor Yellow
    pip install pytest pytest-asyncio httpx
    
    # Run integration tests
    Write-Host "🧪 Running integration tests..." -ForegroundColor Yellow
    try {
        if ($TestPattern -eq "*") {
            python -m pytest tests/integration/ -v --tb=short
        } else {
            python -m pytest tests/integration/ -v --tb=short -k $TestPattern
        }
        
        $exitCode = $LASTEXITCODE
        if ($exitCode -eq 0) {
            Write-Host "✅ All integration tests passed!" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Some integration tests failed" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Error running integration tests: $_" -ForegroundColor Red
        return $false
    }
}

# Main execution
Write-Banner "Recruitly Integration Test Runner"

if ($StopServices) {
    Stop-Services
    exit 0
}

if ($TestOnly) {
    $success = Run-IntegrationTests
    exit $(if ($success) { 0 } else { 1 })
}

if ($StartServices) {
    Write-Banner "Starting Services"
    
    # Start backend
    $backendStarted = Start-BackendService
    if (-not $backendStarted) {
        Write-Host "❌ Failed to start backend" -ForegroundColor Red
        exit 1
    }
    
    # Start frontend
    $frontendStarted = Start-FrontendService
    if (-not $frontendStarted) {
        Write-Host "❌ Failed to start frontend" -ForegroundColor Red
        Stop-Services
        exit 1
    }
    
    Write-Host "`n🎉 All services started successfully!" -ForegroundColor Green
    Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
    
    # Run tests
    $testSuccess = Run-IntegrationTests
    
    # Stop services
    Stop-Services
    
    exit $(if ($testSuccess) { 0 } else { 1 })
} else {
    # Show usage
    Write-Host "USAGE:" -ForegroundColor Yellow
    Write-Host "  .\scripts\run-integration-tests.ps1 -StartServices    # Start services and run tests" -ForegroundColor White
    Write-Host "  .\scripts\run-integration-tests.ps1 -TestOnly         # Run tests only (services must be running)" -ForegroundColor White
    Write-Host "  .\scripts\run-integration-tests.ps1 -StopServices     # Stop all services" -ForegroundColor White
    Write-Host "  .\scripts\run-integration-tests.ps1 -TestPattern 'workflow'  # Run specific tests" -ForegroundColor White
    
    Write-Host "`nEXAMPLES:" -ForegroundColor Yellow
    Write-Host "  # Full integration test run" -ForegroundColor Green
    Write-Host "  .\scripts\run-integration-tests.ps1 -StartServices" -ForegroundColor White
    Write-Host "  # Test specific functionality" -ForegroundColor Green
    Write-Host "  .\scripts\run-integration-tests.ps1 -TestOnly -TestPattern 'health'" -ForegroundColor White
}
