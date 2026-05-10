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

set "APP_DIR=C:\Users\Nuvitaly AQ\Desktop\Panel-Kryon-V2"
cd /d "%APP_DIR%"

set "BACKEND_DIR=%APP_DIR%\backend"
set "FRONTEND_DIR=%APP_DIR%\external-ui"
set "BACKEND_URL=http://localhost:8000/health"
set "WAIT_MAX=60"
set "WAIT_STEP=2"
set "APP_URL=http://localhost:5173/login.html"

echo.
echo [1/3] Liberando puertos...
call :KillPortPS 8000
call :KillPortPS 5173

echo.
echo [2/3] Iniciando Backend (minimizado)...
if exist "%BACKEND_DIR%" (
  start /min "Panel Kryon - Backend" cmd /k "cd /d "%BACKEND_DIR%" && call venv\Scripts\activate && python -m uvicorn app.main:app --reload --port 8000"
) else (
  echo   [!] No existe carpeta "backend" en: %APP_DIR%
  goto :END
)

echo   Esperando que el Backend inicie completamente...
call :WaitForBackend %WAIT_MAX% %WAIT_STEP%
if "!BACKEND_OK!"=="0" (
  echo.
  echo [X] El Backend no respondio a tiempo.
  goto :END
)

echo.
echo [3/3] Iniciando Frontend (minimizado)...
if exist "%FRONTEND_DIR%" (
  start /min "Panel Kryon - Frontend" cmd /c "cd /d "%APP_DIR%" && python -m http.server 5173 --directory external-ui"
) else (
  echo   [!] No existe carpeta "external-ui" en: %APP_DIR%
  goto :END
)

echo.
echo   Esperando 3 segundos para abrir Chrome...
timeout /t 3 >nul

call :OpenChromeFullScreen "%APP_URL%"

goto :END


REM ================= FUNCIONES =================

:OpenChromeFullScreen
set "TARGET_URL=%~1"

REM Cerrar Chrome previo
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 1 >nul

REM Minimizar esta consola ANTES de abrir Chrome
REM GetConsoleWindow esta en kernel32.dll, ShowWindowAsync en user32.dll
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class WA { [DllImport(\"user32.dll\")] public static extern bool ShowWindowAsync(IntPtr h, int n); [DllImport(\"kernel32.dll\")] public static extern IntPtr GetConsoleWindow(); }'; " ^
  "[WA]::ShowWindowAsync([WA]::GetConsoleWindow(), 2) | Out-Null"

REM Abrir Chrome en pantalla completa
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
  start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --start-fullscreen --new-window "%TARGET_URL%"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
  start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --start-fullscreen --new-window "%TARGET_URL%"
) else (
  start "" "%TARGET_URL%"
)

REM Esperar y traer Chrome al frente
timeout /t 3 >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class WF { [DllImport(\"user32.dll\")] public static extern bool SetForegroundWindow(IntPtr h); [DllImport(\"user32.dll\")] public static extern bool ShowWindowAsync(IntPtr h, int n); }'; " ^
  "$p = Get-Process chrome -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1; " ^
  "if($p) { [WF]::ShowWindowAsync($p.MainWindowHandle, 3) | Out-Null; Start-Sleep -Milliseconds 500; [WF]::SetForegroundWindow($p.MainWindowHandle) | Out-Null }"

goto :eof


:WaitForBackend
set /a "MAX=%~1"
set /a "STEP=%~2"
set /a "ELAPSED=0"
set "BACKEND_OK=0"

:WAIT_BACKEND_LOOP
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
echo   Panel Kryon activo. Minimizando consola...
timeout /t 4 >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class WE { [DllImport(\"user32.dll\")] public static extern bool ShowWindowAsync(IntPtr h, int n); [DllImport(\"kernel32.dll\")] public static extern IntPtr GetConsoleWindow(); }'; " ^
  "[WE]::ShowWindowAsync([WE]::GetConsoleWindow(), 2) | Out-Null"
pause >nul
exit /b 0