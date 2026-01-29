@echo off
setlocal

echo ===================================================
echo      STARTING PANEL KRYON
echo ===================================================

cd /d "%~dp0"

:: Check if venv exists
if not exist venv (
    echo [ERROR] Virtual environment 'venv' not found!
    echo Please run 'install.bat' first to set up the project.
    pause
    exit /b 1
)

:: Activate venv
call venv\Scripts\activate

:: Check process on port 8000 and kill if needed
echo [INFO] Checking port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    echo [WARN] Port 8000 is in use by PID %%a. Killing process...
    taskkill /F /PID %%a >nul 2>nul
)

:: Start the server
echo [INFO] Starting Backend Server...
echo.
echo Application will be available at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server.
echo.

:: Open browser (optional, wait a bit for server to start)
start "" "http://localhost:8000"

:: Run Uvicorn
python -m uvicorn app.main:app --reload --port 8000

pause
