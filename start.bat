@echo off
REM Start DataChat – FastAPI backend + Next.js frontend
echo Starting DataChat...

REM Start FastAPI backend
echo [1/2] Starting FastAPI backend on port 8000...
start "DataChat API" cmd /k "cd /d %~dp0DataChat && venv\Scripts\python -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload"

REM Wait 2 seconds for backend to start
timeout /t 2 /nobreak > nul

REM Start Next.js frontend
echo [2/2] Starting Next.js frontend on port 3000...
start "DataChat UI" cmd /k "cd /d %~dp0datachat-ui && npm run dev"

echo.
echo DataChat is starting up!
echo   Frontend: http://localhost:3000
echo   Backend API: http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
pause
