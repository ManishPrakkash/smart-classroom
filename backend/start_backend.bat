@echo off
cd /d "%~dp0"
set USE_MOCK_GPIO=1
set LOG_LEVEL=INFO
set TZ=Asia/Kolkata
"venv\Scripts\python.exe" app.py
pause
