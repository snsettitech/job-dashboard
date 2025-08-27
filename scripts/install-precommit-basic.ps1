Write-Host "Installing Pre-commit Hooks" -ForegroundColor Cyan

# Install pre-commit
Write-Host "Installing pre-commit..." -ForegroundColor Yellow
pip install pre-commit

# Install hooks
Write-Host "Installing hooks..." -ForegroundColor Yellow
pre-commit install

Write-Host "Pre-commit setup complete!" -ForegroundColor Green
