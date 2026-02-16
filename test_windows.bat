@echo off
REM Quick test script for Windows

echo ========================================
echo Smart Classroom - Windows Test Mode
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate venv and install dependencies
echo Installing dependencies...
call venv\Scripts\activate.bat
pip install -q Flask Werkzeug python-dotenv

echo.
echo ========================================
echo Starting server in MOCK MODE...
echo ========================================
echo.
echo Open browser: http://localhost:5000
echo Login: admin / classroom123
echo.
echo Press Ctrl+C to stop
echo.

REM Run the application
python app\app.py

pause
