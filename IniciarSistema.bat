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

echo.
echo [1/2] Preparando Backend (Puerto 8000)...
call :KillPortPS 8000

echo [2/2] Preparando Frontend (Puerto 5173)...
call :KillPortPS 5173

echo.
echo Iniciando servicios...
echo.

echo   Backend...
if exist "backend" (
  pushd "backend"
  start "Panel Kryon - Backend" cmd /c "call venv\Scripts\activate && python -m uvicorn app.main:app --reload --port 8000"
  popd
) else (
  echo   [!] No existe carpeta "backend" en: %cd%
)

timeout /t 2 >nul

echo   Frontend...
start "Panel Kryon - Frontend" cmd /c "python -m http.server 5173 --directory external-ui"

echo.
echo   Esperando 3 segundos para abrir navegador...
timeout /t 3 >nul
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

