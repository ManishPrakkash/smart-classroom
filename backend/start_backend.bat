@echo off
setlocal enabledelayedexpansion

:: ── Smart Switch – Backend Startup (Windows) ──────────────────────────────
:: Double-click or run:  start_backend.bat
:: ──────────────────────────────────────────────────────────────────────────

echo ========================================
echo    Smart Switch - Backend Startup
echo ========================================
echo.

cd /d "%~dp0"

:: ── 1. Load .env ─────────────────────────────────────────────────────────
if exist ".env" (
    echo [1/4] Loading .env ...
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        set "line=%%A"
        if not "!line:~0,1!"=="#" (
            set "%%A=%%~B"
        )
    )
    echo       Done.
) else (
    echo [1/4] No .env file found - using system environment.
)
echo.

:: ── 2. Virtual environment ────────────────────────────────────────────────
echo [2/4] Checking virtual environment ...
if not exist "venv\Scripts\activate.bat" (
    echo       Creating virtual environment ...
    py -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment. Is Python installed?
        pause
        exit /b 1
    )
) else (
    echo       Virtual environment already exists.
)

call venv\Scripts\activate.bat
echo       Active: %VIRTUAL_ENV%
echo.

:: ── 3. Install dependencies ───────────────────────────────────────────────
echo [3/4] Installing dependencies from requirements.txt ...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo       Done.
echo.

:: ── 4. Start Flask app ────────────────────────────────────────────────────
echo [4/4] Starting Flask backend ...
echo       Mock GPIO enabled (Windows dev mode).
echo       Server will be available at http://localhost:8000
echo.

set USE_MOCK_GPIO=1
py app.py

pause
