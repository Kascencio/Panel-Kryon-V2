@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ===================================================
REM  PANEL KRYON - AUTO-INICIO CON WINDOWS
REM ===================================================
REM  Coloca este archivo en:
REM  C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp
REM  
REM  El proyecto debe estar en: C:\Panel-Kryon-V2
REM ===================================================

REM ========= CONFIGURACIÓN =========
set "PANEL_PATH=C:\Panel-Kryon-V2"
set "BACKEND_URL=http://localhost:8000/health"
set "WAIT_MAX=60"
set "WAIT_STEP=3"
REM =================================

REM Esperar un poco para que Windows cargue completamente
echo Esperando 10 segundos para que Windows inicie completamente...
timeout /t 10 /nobreak >nul

echo ===================================================
echo     INICIANDO PANEL KRYON (Auto-Inicio)
echo ===================================================

cd /d "%PANEL_PATH%"

REM Verificar que existe la carpeta
if not exist "%PANEL_PATH%\backend" (
    echo [X] No se encontro Panel Kryon en: %PANEL_PATH%
    echo     Verifica la ruta en este archivo.
    pause
    exit /b 1
)

echo.
echo [1/3] Liberando puertos...
call :KillPortPS 8000
call :KillPortPS 5173

echo.
echo [2/3] Iniciando Backend...
pushd "%PANEL_PATH%\backend"
start /min "Panel Kryon - Backend" cmd /c "call venv\Scripts\activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
popd

echo   Esperando que el Backend inicie...
call :WaitForBackend %WAIT_MAX% %WAIT_STEP%
if "!BACKEND_OK!"=="0" (
    echo [X] El Backend no respondio. Revisa los logs.
    pause
    exit /b 1
)

echo.
echo [3/3] Iniciando Frontend...
start /min "Panel Kryon - Frontend" cmd /c "python -m http.server 5173 --directory %PANEL_PATH%\external-ui"

echo.
echo   Esperando 3 segundos...
timeout /t 3 /nobreak >nul

REM Abrir navegador
start "" "http://localhost:5173/login.html"

echo.
echo ===================================================
echo   PANEL KRYON INICIADO CORRECTAMENTE
echo ===================================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   Login:    http://localhost:5173/login.html
echo ===================================================

REM Cerrar esta ventana después de 5 segundos
timeout /t 5 /nobreak >nul
exit /b 0


REM ================= FUNCIONES =================

:WaitForBackend
set /a "MAX=%~1"
set /a "STEP=%~2"
set /a "ELAPSED=0"
set "BACKEND_OK=0"

:WAIT_LOOP
curl -s -o nul -w "" "%BACKEND_URL%" >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    set "BACKEND_OK=1"
    echo   Backend listo.
    goto :eof
)

if !ELAPSED! GEQ !MAX! (
    echo   Timeout esperando Backend.
    goto :eof
)

echo   Esperando... !ELAPSED!/!MAX! seg
timeout /t !STEP! /nobreak >nul
set /a "ELAPSED+=STEP"
goto :WAIT_LOOP


:KillPortPS
set "PORT=%~1"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$p = Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; " ^
  "if($p){ $p | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }; Write-Host '   Puerto %PORT% liberado' } else { Write-Host '   Puerto %PORT% libre' }"
exit /b
