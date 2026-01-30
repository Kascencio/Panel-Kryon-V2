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
set "XAMPP_DIR=C:\xampp"
set "XAMPP_CTRL=%XAMPP_DIR%\xampp-control.exe"

REM Considerar XAMPP listo si MySQL (3306) está escuchando
set "PORT_MYSQL=3306"

REM Tiempo máximo de espera (segundos)
set "WAIT_MAX=60"
set "WAIT_STEP=2"
REM ===========================

echo.
echo [0/3] Verificando XAMPP (MySQL puerto %PORT_MYSQL%)...

call :IsPortListening %PORT_MYSQL%
if "!PORT_OK!"=="1" goto :START_APPS

echo   MySQL no está arriba. Intentando iniciar servicios (si existen)...
call :StartXamppServices

call :WaitPort %PORT_MYSQL% %WAIT_MAX% %WAIT_STEP%
if "!PORT_OK!"=="1" goto :START_APPS

echo   No se logro por servicios. Abriendo XAMPP Control...
if exist "%XAMPP_CTRL%" (
  start "" "%XAMPP_CTRL%"
) else (
  echo   [!] No se encontro: "%XAMPP_CTRL%"
)

call :WaitPort %PORT_MYSQL% %WAIT_MAX% %WAIT_STEP%
if "!PORT_OK!"=="1" goto :START_APPS

echo.
echo [X] XAMPP/MySQL NO quedo listo.
echo     - Abre XAMPP como Administrador
echo     - Enciende MySQL y revisa que %PORT_MYSQL% no este ocupado
echo.
goto :END


:START_APPS
echo.
echo [1/3] Preparando Backend...
call :KillPortPS 8000

echo [2/3] Preparando Frontend...
call :KillPortPS 5173

echo [3/3] Iniciando servicios...
echo.

echo   Backend (Puerto 8000)...
if exist "backend" (
  pushd "backend"
  start "Panel Kryon - Backend" cmd /c "call venv\Scripts\activate && python -m uvicorn app.main:app --reload --port 8000"
  popd
) else (
  echo   [!] No existe carpeta "backend" en: %cd%
)

timeout /t 2 >nul

echo   Frontend (Puerto 5173)...
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
echo.
goto :END


REM ================= FUNCIONES =================

:IsPortListening
set "PORT=%~1"
set "PORT_OK=0"
for /f "tokens=1" %%L in ('netstat -ano ^| findstr /R /C:":%PORT% .*LISTENING" 2^>nul') do (
  set "PORT_OK=1"
  goto :eof
)
goto :eof

:WaitPort
REM Uso: call :WaitPort 3306 60 2
set "PORT=%~1"
set /a "MAX=%~2"
set /a "STEP=%~3"
set /a "ELAPSED=0"

:WAIT_LOOP
call :IsPortListening %PORT%
if "!PORT_OK!"=="1" (
  echo   OK: Puerto %PORT% LISTENING.
  goto :eof
)

if !ELAPSED! GEQ !MAX! (
  echo   [!] Timeout esperando puerto %PORT%.
  goto :eof
)

echo   Esperando puerto %PORT%... !ELAPSED!/!MAX! seg
timeout /t !STEP! >nul
set /a "ELAPSED+=STEP"
goto :WAIT_LOOP

:StartXamppServices
REM Nota: Requiere permisos de admin si los servicios existen
sc query "mysql" >nul 2>nul && (
  echo   -> net start mysql
  net start "mysql" >nul 2>nul
)
sc query "mariadb" >nul 2>nul && (
  echo   -> net start mariadb
  net start "mariadb" >nul 2>nul
)
sc query "Apache2.4" >nul 2>nul && (
  echo   -> net start Apache2.4
  net start "Apache2.4" >nul 2>nul
)
goto :eof

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
