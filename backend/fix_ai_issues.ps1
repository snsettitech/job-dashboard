# PowerShell script to fix AI issues
Write-Host "🔧 RECRUITLY AI ISSUE FIXER" -ForegroundColor Green
Write-Host "=" * 40

# Activate virtual environment
Write-Host "`n1. Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Check if activation worked
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

# Fix numpy compatibility
Write-Host "`n2. Fixing numpy compatibility..." -ForegroundColor Yellow
pip install "numpy<2.0" --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Numpy downgraded to compatible version" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to fix numpy" -ForegroundColor Red
}

# Test imports
Write-Host "`n3. Testing imports..." -ForegroundColor Yellow
python -c @"
import numpy as np
print(f'numpy {np.__version__}')

from sklearn.metrics.pairwise import cosine_similarity
print('sklearn working')

import openai
print(f'openai {openai.__version__}')

from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
if api_key and api_key.startswith('proj-'):
    print(f'API key loaded: {api_key[:15]}...')
else:
    print(f'API key issue: {api_key[:20] if api_key else \"None\"}...')
"@

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nALL FIXES SUCCESSFUL!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "1. Stop your current server (Ctrl+C if running)" -ForegroundColor White
    Write-Host "2. Restart with: python main.py" -ForegroundColor White
    Write-Host "3. Test AI optimization in the frontend" -ForegroundColor White
    Write-Host "4. Look for 'Mounted modular AI router' message" -ForegroundColor White
} else {
    Write-Host "`nSome issues remain. Check the output above." -ForegroundColor Red
}
