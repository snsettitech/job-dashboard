@echo off
REM Backend test runner for pre-commit hooks (Windows)

echo 🧪 Running backend tests...

REM Change to backend directory
cd backend
if errorlevel 1 exit /b 1

REM Check if virtual environment exists and activate it
if exist "venv\Scripts\activate.bat" (
    echo 🐍 Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Run basic tests that should always pass
echo 🔍 Running basic tests...
python -m pytest tests/test_basic.py -v --tb=short

if %errorlevel% equ 0 (
    echo ✅ Backend tests passed
) else (
    echo ❌ Backend tests failed
    echo 💡 Fix tests before committing
    exit /b %errorlevel%
)

exit /b 0
