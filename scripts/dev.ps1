# Recruitly Development Workflow PowerShell Wrapper
param(
    [Parameter(Mandatory=$false, Position=0)]
    [string]$Action,

    [Parameter(Mandatory=$false)]
    [string]$Feature,

    [Parameter(Mandatory=$false)]
    [string]$Description,

    [Parameter(Mandatory=$false)]
    [string[]]$Files,

    [Parameter(Mandatory=$false)]
    [string]$Notes,

    [Parameter(Mandatory=$false)]
    [string]$Message
)

function Write-Banner {
    param([string]$Message)
    Write-Host "`n🚀 $Message" -ForegroundColor Cyan
    Write-Host ("=" * ($Message.Length + 4)) -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

# Main execution
if (-not $Action) {
    Write-Banner "Recruitly Development Workflow"
    Write-Host "USAGE: .\scripts\dev.ps1 [action] [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "ACTIONS:" -ForegroundColor Yellow
    Write-Host "  status    - Show project status" -ForegroundColor White
    Write-Host "  test      - Run test suite" -ForegroundColor White
    Write-Host "  start     - Start new feature" -ForegroundColor White
    Write-Host "  complete  - Complete feature" -ForegroundColor White
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Yellow
    Write-Host "  .\scripts\dev.ps1 status" -ForegroundColor White
    Write-Host "  .\scripts\dev.ps1 test" -ForegroundColor White
    exit 0
}

Write-Banner "Recruitly Development Workflow"

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python found: $pythonVersion"
} catch {
    Write-Error "Python not found in PATH"
    exit 1
}

# Check if dev-workflow.py exists
if (-not (Test-Path "scripts/dev-workflow.py")) {
    Write-Error "dev-workflow.py not found. Run from project root."
    exit 1
}

# Build Python command
$pythonArgs = @("scripts/dev-workflow.py", $Action)

# Add parameters
if ($Feature) {
    $pythonArgs += "--feature"
    $pythonArgs += $Feature
}
if ($Description) {
    $pythonArgs += "--description"
    $pythonArgs += $Description
}
if ($Files) {
    $pythonArgs += "--files"
    $pythonArgs += ($Files -join ",")
}
if ($Notes) {
    $pythonArgs += "--notes"
    $pythonArgs += $Notes
}
if ($Message) {
    $pythonArgs += "--message"
    $pythonArgs += $Message
}

Write-Host "🐍 Executing: python $($pythonArgs -join ' ')" -ForegroundColor Cyan

try {
    # Execute Python script
    & python $pythonArgs
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Success "Command completed successfully"
    } else {
        Write-Error "Command failed with exit code: $exitCode"
        exit $exitCode
    }
} catch {
    Write-Error "Failed to execute Python script: $_"
    exit 1
}

Write-Host "`n✅ Workflow completed!" -ForegroundColor Green
