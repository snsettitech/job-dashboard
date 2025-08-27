# Pre-commit hooks setup script for Recruitly
param(
    [switch]$Install,
    [switch]$Test,
    [switch]$Uninstall
)

function Write-Banner {
    param([string]$Message)
    Write-Host "`n🔧 $Message" -ForegroundColor Cyan
    Write-Host ("=" * ($Message.Length + 4)) -ForegroundColor Cyan
}

function Test-PreCommitInstallation {
    Write-Host "🔍 Checking pre-commit installation..." -ForegroundColor Yellow

    try {
        $version = pre-commit --version
        Write-Host "✅ pre-commit found: $version" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ pre-commit not found" -ForegroundColor Red
        return $false
    }
}

function Install-PreCommit {
    Write-Banner "Installing Pre-commit Hooks"

    # Check if pre-commit is installed
    if (-not (Test-PreCommitInstallation)) {
        Write-Host "📦 Installing pre-commit..." -ForegroundColor Yellow
        try {
            pip install pre-commit
            Write-Host "✅ pre-commit installed" -ForegroundColor Green
        } catch {
            Write-Host "❌ Failed to install pre-commit" -ForegroundColor Red
            return $false
        }
    }

    # Install hooks
    Write-Host "🔗 Installing pre-commit hooks..." -ForegroundColor Yellow
    try {
        pre-commit install
        Write-Host "✅ Pre-commit hooks installed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install hooks" -ForegroundColor Red
        return $false
    }

    # Make scripts executable (Windows doesn't need this, but good practice)
    $scripts = @(
        "scripts/run-backend-tests.bat",
        "scripts/run-frontend-tests.bat"
    )

    foreach ($script in $scripts) {
        if (Test-Path $script) {
            Write-Host "✅ Script ready: $script" -ForegroundColor Green
        } else {
            Write-Host "❌ Script missing: $script" -ForegroundColor Red
        }
    }

    return $true
}

function Test-PreCommitHooks {
    Write-Banner "Testing Pre-commit Hooks"

    if (-not (Test-PreCommitInstallation)) {
        Write-Host "❌ pre-commit not installed" -ForegroundColor Red
        return $false
    }

    Write-Host "🧪 Running pre-commit on all files..." -ForegroundColor Yellow
    try {
        pre-commit run --all-files
        Write-Host "✅ Pre-commit tests completed" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Pre-commit tests failed" -ForegroundColor Red
        return $false
    }
}

function Uninstall-PreCommit {
    Write-Banner "Uninstalling Pre-commit Hooks"

    try {
        pre-commit uninstall
        Write-Host "✅ Pre-commit hooks uninstalled" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Failed to uninstall hooks" -ForegroundColor Red
        return $false
    }
}

function Show-PreCommitStatus {
    Write-Banner "Pre-commit Status"

    # Check installation
    $installed = Test-PreCommitInstallation
    Write-Host "Pre-commit installed: $(if ($installed) { '✅' } else { '❌' })" -ForegroundColor $(if ($installed) { 'Green' } else { 'Red' })

    # Check hooks
    if ($installed) {
        try {
            $hooks = pre-commit run --all-files --dry-run 2>&1
            Write-Host "✅ Hooks configured and ready" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ Hooks may need configuration" -ForegroundColor Yellow
        }
    }

    # Check config file
    if (Test-Path ".pre-commit-config.yaml") {
        Write-Host "✅ Configuration file exists" -ForegroundColor Green
    } else {
        Write-Host "❌ Configuration file missing" -ForegroundColor Red
    }

    # Check scripts
    $scripts = @(
        "scripts/run-backend-tests.bat",
        "scripts/run-frontend-tests.bat",
        "scripts/update-context.sh"
    )

    Write-Host "`nScript Status:" -ForegroundColor Yellow
    foreach ($script in $scripts) {
        $exists = Test-Path $script
        $status = if ($exists) { '✅' } else { '❌' }
        $color = if ($exists) { 'Green' } else { 'Red' }
        Write-Host "  $script`: $status" -ForegroundColor $color
    }
}

# Main execution
if ($Install) {
    $success = Install-PreCommit
    if ($success) {
        Write-Host "`n🎉 Pre-commit hooks setup complete!" -ForegroundColor Green
        Write-Host "Now your commits will automatically:" -ForegroundColor Cyan
        Write-Host "  ✅ Run backend tests" -ForegroundColor White
        Write-Host "  ✅ Run frontend tests" -ForegroundColor White
        Write-Host "  ✅ Format code with Black and Prettier" -ForegroundColor White
        Write-Host "  ✅ Update development context" -ForegroundColor White
        Write-Host "  ✅ Check for common issues" -ForegroundColor White
    }
} elseif ($Test) {
    Test-PreCommitHooks
} elseif ($Uninstall) {
    Uninstall-PreCommit
} else {
    Show-PreCommitStatus
    Write-Host "`nUSAGE:" -ForegroundColor Yellow
    Write-Host "  .\scripts\setup-precommit.ps1 -Install    # Install pre-commit hooks" -ForegroundColor White
    Write-Host "  .\scripts\setup-precommit.ps1 -Test       # Test hooks on all files" -ForegroundColor White
    Write-Host "  .\scripts\setup-precommit.ps1 -Uninstall  # Remove hooks" -ForegroundColor White
    Write-Host "  .\scripts\setup-precommit.ps1             # Show status" -ForegroundColor White
}
