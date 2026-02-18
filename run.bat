@echo off
echo Starting Smart-Switch...

echo Starting Flask backend...
start "Smart-Switch Backend" powershell -NoExit -Command "cd '%~dp0backend'; python app.py"

echo Starting Vite frontend...
start "Smart-Switch Frontend" powershell -NoExit -Command "cd '%~dp0frontend'; npm run dev"

echo Both servers launched.
echo   Backend:  http://localhost:5000
echo   Frontend: http://localhost:5173
