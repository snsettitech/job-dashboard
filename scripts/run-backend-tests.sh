#!/bin/bash
# Backend test runner for pre-commit hooks

echo "🧪 Running backend tests..."

# Change to backend directory
cd backend || exit 1

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate || source venv/Scripts/activate
fi

# Run basic tests that should always pass
echo "🔍 Running basic tests..."
python -m pytest tests/test_basic.py -v --tb=short

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ Backend tests passed"
else
    echo "❌ Backend tests failed"
    echo "💡 Fix tests before committing"
fi

exit $exit_code
