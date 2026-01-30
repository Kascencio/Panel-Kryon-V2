@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo ===================================================
echo            INICIANDO PANEL KRYON
echo ===================================================

cd /d "%~dp0"

REM ========= CONFIG =========
set "XAMPP_DIR=C:\xampp"
set "XAMPP_CTRL=%XAMPP_DIR%\xampp-control.exe"

REM Qué considerar "XAMPP listo"
set "CHECK_MYSQL=1"
set "CHECK_APACHE=0"

REM Puertos típicos
set "PORT_MYSQL=3306"
set "PORT_APACHE=80"

REM Tiempo máximo de espera (segundos)
set "WAIT_MAX=60"
REM Intervalo entre intentos (segundos)
set "WAIT_STEP=2"
REM ===========================


REM ---------------------------------------------------
REM 0) FUNCIONES (como labels)
REM ---------------------------------------------------
goto :MAIN

:IsPortListening
REM Uso: call :IsPortListening 3306 RESULTVAR
set "P=%~1"
set "OUTVAR=%~2"
set "FOUND=0"
for /f "tokens=5" %%a in ('netstat -aon ^| find ":%P%" ^| find "LISTENING" 2^>nul') do (
  set "FOUND=1"
  goto :PortDone
)
:PortDone
set "%OUTVAR%=%FOUND%"
exit /b

:StartXamppServices
REM Intenta iniciar servicios si existen
REM Apache service (puede llamarse Apache2.4)
sc query "Apache2.4" >nul 2>nul && (
  echo   Iniciando servicio Apache2.4...
  net start "Apache2.4" >nul 2>nul
)

REM MySQL service (en XAMPP suele ser mysql)
sc query "mysql" >nul 2>nul && (
  echo   Iniciando servicio mysql...
  net start "mysql" >nul 2>nul
)

REM MariaDB en algunas instalaciones
sc query "mariadb" >nul 2>nul && (
  echo   Iniciando servicio mariadb...
  net start "mariadb" >nul 2>nul
)

exit /b

:OpenXamppControlAdmin
REM Abre el panel (si existe). Intento normal; si ya lo tienes en compatibilidad "admin", pedirá UAC.
if exist "%XAMPP_CTRL%" (
  echo   Abriendo XAMPP Control...
  start "" "%XAMPP_CTRL%"
) else (
  echo   [!] No se encontro xampp-control.exe en: "%XAMPP_CTRL%"
)
exit /b

:WaitForXamppReady
REM Espera hasta que los puertos requeridos estén LISTENING
set /a "ELAPSED=0"

:WaitLoop
set "OK=1"

if "%CHECK_MYSQL%"=="1" (
  call :IsPortListening %PORT_MYSQL% MYSQL_UP
  if "!MYSQL_UP!"=="0" set "OK=0"
)

if "%CHECK_APACHE%"=="1" (
  call :IsPortListening %PORT_APACHE% APACHE_UP
  if "!APACHE_UP!"=="0" set "OK=0"
)

if "!OK!"=="1" (
  echo   XAMPP listo (puertos OK).
  exit /b 0
)

if %ELAPSED% GEQ %WAIT_MAX% (
  echo   [X] Tiempo agotado. XAMPP NO quedo listo.
  exit /b 1
)

echo   Esperando XAMPP... %ELAPSED%/%WAIT_MAX% seg
timeout /t %WAIT_STEP% >nul
set /a "ELAPSED+=%WAIT_STEP%"
goto :WaitLoop


:KillPort
REM Uso: call :KillPort 8000
set "KP=%~1"
for /f "tokens=5" %%a in ('netstat -aon ^| find ":%KP%" ^| find "LISTENING" 2^>nul') do (
  echo   Matando proceso en puerto %KP% (PID %%a)...
  taskkill /F /PID %%a >nul 2>nul
)
exit /b

:MAIN
echo.
echo [0/3] Verificando XAMPP...

REM 0.1) Si ya está listo, seguimos
call :WaitForXamppReady
if %errorlevel%==0 goto :START_APPS

REM 0.2) Intentar iniciar servicios
echo   XAMPP no esta listo. Intentando iniciar servicios...
call :StartXamppServices

REM Reintentar espera
call :WaitForXamppReady
if %errorlevel%==0 goto :START_APPS

REM 0.3) Abrir panel XAMPP como fallback
echo   No se logro iniciar por servicios. Abriendo panel XAMPP...
call :OpenXamppControlAdmin

REM Reintentar espera final
call :WaitForXamppReady
if not %errorlevel%==0 (
  echo.
  echo [X] No se pudo verificar XAMPP listo. Revisa:
  echo     - Que MySQL este iniciado en XAMPP
  echo     - Que el puerto %PORT_MYSQL% no este ocupado
  echo.
  pause
  exit /b 1
)

:START_APPS
REM ---------------------------------------------------
REM 1. VERIFICAR Y MATAR PUERTO 8000 (Backend)
REM ---------------------------------------------------
echo.
echo [1/3] Preparando Backend...
call :KillPort 8000

REM ---------------------------------------------------
REM 2. VERIFICAR Y MATAR PUERTO 5173 (Frontend)
REM ---------------------------------------------------
echo [2/3] Preparando Frontend...
call :KillPort 5173

REM ---------------------------------------------------
REM 3. INICIAR BACKEND
REM ---------------------------------------------------
echo [3/3] Iniciando servicios...
echo.

echo   Backend (Puerto 8000)...
cd backend
start "Panel Kryon - Backend" cmd /c "call venv\Scripts\activate && python -m uvicorn app.main:app --reload --port 8000"
cd ..

timeout /t 2 >nul

REM ---------------------------------------------------
REM 4. INICIAR FRONTEND
REM ---------------------------------------------------
echo   Frontend (Puerto 5173)...
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
pause
exit /b 0
