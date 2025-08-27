# Husky Setup for Git Hooks
Write-Host "Setting up Git hooks with Husky..." -ForegroundColor Cyan

# Check if Node.js is available
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js first." -ForegroundColor Red
    exit 1
}

# Install Husky
Write-Host "Installing Husky..." -ForegroundColor Yellow
npm install husky --save-dev

# Install commitlint
Write-Host "Installing commitlint..." -ForegroundColor Yellow
npm install @commitlint/cli @commitlint/config-conventional --save-dev

# Initialize Husky
Write-Host "Initializing Husky..." -ForegroundColor Yellow
npx husky install

# Make hooks executable
if (Test-Path ".husky/commit-msg") {
    Write-Host "Making commit-msg hook executable..." -ForegroundColor Yellow
    # On Windows, this is handled by Git automatically
}

if (Test-Path ".husky/pre-commit") {
    Write-Host "Making pre-commit hook executable..." -ForegroundColor Yellow
    # On Windows, this is handled by Git automatically
}

Write-Host "✅ Git hooks setup complete!" -ForegroundColor Green
Write-Host "📝 Commit messages will now be validated against conventional commit format" -ForegroundColor Blue
Write-Host "🔍 Pre-commit hooks will run code quality checks before each commit" -ForegroundColor Blue
