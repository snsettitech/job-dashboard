@echo off
REM Frontend test runner for pre-commit hooks (Windows)

echo 🧪 Running frontend tests...

REM Change to frontend directory
cd frontend
if errorlevel 1 exit /b 1

REM Check if node_modules exists
if not exist "node_modules" (
    echo ❌ node_modules not found. Run 'npm install' first.
    exit /b 1
)

REM Run tests without watch mode
echo 🔍 Running React tests...
npm test -- --watchAll=false --coverage=false --verbose=false

if %errorlevel% equ 0 (
    echo ✅ Frontend tests passed
) else (
    echo ❌ Frontend tests failed
    echo 💡 Fix tests before committing
    exit /b %errorlevel%
)

exit /b 0
