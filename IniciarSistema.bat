@echo off
setlocal

echo ===================================================
echo      INICIANDO PANEL KRYON
echo ===================================================

cd /d "%~dp0"

REM ---------------------------------------------------
REM 1. VERIFICAR Y MATAR PUERTO 8000 (Backend)
REM ---------------------------------------------------
echo.
echo [1/3] Preparando Backend...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    echo   Matando proceso en puerto 8000 ^(PID %%a^)...
    taskkill /F /PID %%a >nul 2>nul
)

REM ---------------------------------------------------
REM 2. VERIFICAR Y MATAR PUERTO 5173 (Frontend)
REM ---------------------------------------------------
echo [2/3] Preparando Frontend...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5173" ^| find "LISTENING"') do (
    echo   Matando proceso en puerto 5173 ^(PID %%a^)...
    taskkill /F /PID %%a >nul 2>nul
)

REM ---------------------------------------------------
REM 3. INICIAR BACKEND
REM ---------------------------------------------------
echo [3/3] Iniciando servicios...
echo.

echo   Backend ^(Puerto 8000^)...
cd backend
start "Panel Kryon - Backend" cmd /c "call venv\Scripts\activate && python -m uvicorn app.main:app --reload --port 8000"
cd ..

REM Esperar un poco para que el backend inicie
timeout /t 2 >nul

REM ---------------------------------------------------
REM 4. INICIAR FRONTEND
REM ---------------------------------------------------
echo   Frontend ^(Puerto 5173^)...
start "Panel Kryon - Frontend" cmd /c "python -m http.server 5173 --directory external-ui"

REM ---------------------------------------------------
REM 5. ABRIR NAVEGADOR
REM ---------------------------------------------------
echo.
echo   Esperando 3 segundos para abrir navegador...
timeout /t 3 >nul

start "" "http://localhost:5173/login.html"

echo.
echo ===================================================
echo   PANEL KRYON INICIADO
echo ===================================================
echo.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   Login:    http://localhost:5173/login.html
echo.
echo   Para detener, cierra las ventanas de terminal
echo   tituladas "Panel Kryon - Backend" y "Panel Kryon - Frontend"
echo.
pause
