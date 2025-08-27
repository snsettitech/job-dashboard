@echo off
echo 🔧 RECRUITLY AI ISSUE FIXER
echo ========================================

echo.
echo 1. Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo 2. Fixing numpy compatibility...
pip install "numpy<2.0" --quiet

echo.
echo 3. Testing imports...
python -c "import numpy as np; print(f'✅ numpy {np.__version__}')"
python -c "from sklearn.metrics.pairwise import cosine_similarity; print('✅ sklearn working')"
python -c "import openai; print(f'✅ openai {openai.__version__}')"
python -c "from dotenv import load_dotenv; import os; load_dotenv(); api_key = os.getenv('OPENAI_API_KEY'); print(f'✅ API key: {api_key[:15]}...' if api_key and api_key.startswith('proj-') else '❌ API key issue')"

echo.
echo 🎉 FIXES COMPLETE!
echo.
echo 📋 Next steps:
echo 1. Stop your current server (Ctrl+C if running)
echo 2. Restart with: python main.py
echo 3. Test AI optimization in the frontend
echo 4. Look for "Mounted modular AI router" message
echo.
pause
