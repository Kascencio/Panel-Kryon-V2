@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo      PANEL KRYON - INSTALLATION START
echo ===================================================

cd /d "%~dp0"

REM ---------------------------------------------------
REM 1. CHECK & INSTALL VISUAL C++ BUILD TOOLS
REM ---------------------------------------------------
echo.
echo [1/4] Checking Visual C++ Build Tools...

REM Flag to track if we need to install C++ tools
set "NEED_CPP=1"

REM Check validation method 1: vswhere (The proper way)
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" (
    REM Check if VC Tools component is present
    for /f "usebackq tokens=*" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do (
        set "NEED_CPP=0"
    )
)

REM Check validation method 2: Fallback to checking cl.exe if vswhere is missing but maybe cl is in path
if "!NEED_CPP!"=="1" (
    where cl >nul 2>nul
    if !errorlevel! equ 0 (
        set "NEED_CPP=0"
    )
)

if "!NEED_CPP!"=="1" (
    echo    - C++ Build Tools not detected.
    echo    - Downloading and installing Visual C++ Build Tools...
    echo    - This may take a while ^(1-2 GB download^). Please wait...
    
    REM Download vs_buildtools.exe
    powershell -Command "Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vs_buildtools.exe' -OutFile 'vs_buildtools.exe'"
    
    REM Install silently
    start /wait vs_buildtools.exe --passive --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --norestart
    
    echo    - Visual C++ Build Tools installation finished.
    if exist vs_buildtools.exe del vs_buildtools.exe
) else (
    echo    - Visual C++ Build Tools are already installed.
)

REM ---------------------------------------------------
REM 2. CHECK & INSTALL RUST & CARGO
REM ---------------------------------------------------
echo.
echo [2/4] Checking Rust and Cargo...

where cargo >nul 2>nul
if %errorlevel% neq 0 (
    echo    - Cargo/Rust not found.
    echo    - Downloading Rustup...
    
    REM Download rustup
    powershell -Command "Invoke-WebRequest -Uri 'https://win.rustup.rs/x86_64' -OutFile 'rustup-init.exe'"
    
    REM Install silently
    echo    - Installing Rust...
    start /wait rustup-init.exe -y
    
    echo    - Rust installed.
    if exist rustup-init.exe del rustup-init.exe
    
    REM Update PATH for current session
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
) else (
    echo    - Rust is already installed.
)

REM ---------------------------------------------------
REM 3. CHECK & INSTALL PYTHON
REM ---------------------------------------------------
echo.
echo [3/4] Checking Python...

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo    - Python not found.
    echo    - Downloading Python 3.12 installer...
    
    REM Download Python installer
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.1/python-3.12.1-amd64.exe' -OutFile 'python_installer.exe'"
    
    REM Install silently
    echo    - Installing Python...
    start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    echo    - Python installed.
    if exist python_installer.exe del python_installer.exe
) else (
    echo    - Python is already installed.
)

REM ---------------------------------------------------
REM 4. SETUP VENV AND INSTALL DEPENDENCIES
REM ---------------------------------------------------
echo.
echo [4/4] Setting up Project Environment...

REM Check if python is available now
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python was installed but is not visible in the current session.
    echo Please RESTART this script or your computer to finalize the setup.
    pause
    exit /b 1
)

if not exist venv (
    echo    - Creating virtual environment 'venv'...
    python -m venv venv
) else (
    echo    - Virtual environment 'venv' already exists.
)

echo    - Activating venv...
call venv\Scripts\activate

echo    - Upgrading pip...
python -m pip install --upgrade pip

echo    - Installing requirements...
pip install -r requirements.txt

REM Optional: Initialize DB
if exist reset_db.py (
    echo    - Initializing Database...
    python reset_db.py
)

echo.
echo ===================================================
echo      INSTALLATION COMPLETE!
echo ===================================================
echo You can now run the application using 'run.bat'
echo.
pause
