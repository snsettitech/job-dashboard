#!/bin/bash
# Frontend test runner for pre-commit hooks

echo "🧪 Running frontend tests..."

# Change to frontend directory
cd frontend || exit 1

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "❌ node_modules not found. Run 'npm install' first."
    exit 1
fi

# Run tests without watch mode
echo "🔍 Running React tests..."
npm test -- --watchAll=false --coverage=false --verbose=false

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ Frontend tests passed"
else
    echo "❌ Frontend tests failed"
    echo "💡 Fix tests before committing"
fi

exit $exit_code
