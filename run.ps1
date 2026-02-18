# Smart-Switch - Start Backend and Frontend
Write-Host "Starting Smart-Switch..." -ForegroundColor Cyan

# Start Backend
Write-Host "Starting Flask backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python app.py" -WindowStyle Normal

# Start Frontend
Write-Host "Starting Vite frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev" -WindowStyle Normal

Write-Host "Both servers launched in separate windows." -ForegroundColor Green
Write-Host "  Backend: http://localhost:5000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
