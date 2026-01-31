@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ===================================================
REM  AUTO-REABRIR EN CONSOLA PERSISTENTE (NO SE CIERRA)
REM ===================================================
if /i "%~1" NEQ "RUN" (
  title Panel Kryon Launcher
  cmd /k "%~f0" RUN
  exit /b
)

echo ===================================================
echo            INICIANDO PANEL KRYON
echo ===================================================

cd /d "%~dp0"

REM ========= CONFIG =========
set "BACKEND_URL=http://localhost:8000/health"
set "WAIT_MAX=60"
set "WAIT_STEP=2"
REM ==========================

echo.
echo [1/3] Liberando puertos...
call :KillPortPS 8000
call :KillPortPS 5173

echo.
echo [2/3] Iniciando Backend...
if exist "backend" (
  pushd "backend"
  start "Panel Kryon - Backend" cmd /c "call venv\Scripts\activate && python -m uvicorn app.main:app --reload --port 8000"
  popd
) else (
  echo   [!] No existe carpeta "backend" en: %cd%
  goto :END
)

echo   Esperando que el Backend inicie completamente...
call :WaitForBackend %WAIT_MAX% %WAIT_STEP%
if "!BACKEND_OK!"=="0" (
  echo.
  echo [X] El Backend no respondio a tiempo.
  echo     Revisa la ventana del Backend para ver errores.
  goto :END
)

echo.
echo [3/3] Iniciando Frontend...
start "Panel Kryon - Frontend" cmd /c "python -m http.server 5173 --directory external-ui"

echo.
echo   Esperando 2 segundos para abrir navegador...
timeout /t 2 >nul
start "" "http://localhost:5173/login.html"

echo.
echo ===================================================
echo   PANEL KRYON INICIADO
echo ===================================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   Login:    http://localhost:5173/login.html
echo   API Docs: http://localhost:8000/docs
echo.
echo   Base de datos: SQLite (panel_kryon.db)
echo.
goto :END


REM ================= FUNCIONES =================

:WaitForBackend
set /a "MAX=%~1"
set /a "STEP=%~2"
set /a "ELAPSED=0"
set "BACKEND_OK=0"

:WAIT_BACKEND_LOOP
REM Intentar conectar al health endpoint
curl -s -o nul -w "" "%BACKEND_URL%" >nul 2>&1
if !ERRORLEVEL! EQU 0 (
  set "BACKEND_OK=1"
  echo   OK: Backend listo.
  goto :eof
)

if !ELAPSED! GEQ !MAX! (
  echo   [!] Timeout esperando Backend.
  goto :eof
)

echo   Esperando Backend... !ELAPSED!/!MAX! seg
timeout /t !STEP! >nul
set /a "ELAPSED+=STEP"
goto :WAIT_BACKEND_LOOP

:KillPortPS
set "KP=%~1"
echo   Verificando puerto %KP%...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$p = Get-NetTCPConnection -LocalPort %KP% -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; " ^
  "if($p){ $p | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }; Write-Host '   Matado(s) PID:' ($p -join ', ') } else { Write-Host '   Puerto libre.' }"
exit /b


:END
echo.
echo (Presiona una tecla para cerrar esta ventana)
pause >nul
exit /b 0
