@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo      PANEL KRYON - INSTALLATION START
echo ===================================================

cd /d "%~dp0"

REM ---------------------------------------------------
REM 1. CHECK & INSTALL VISUAL C++ BUILD TOOLS + SDK
REM ---------------------------------------------------
echo.
echo [1/4] Checking Visual C++ Build Tools...

set "VS_PATH="
set "NEED_CPP=1"
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"

REM Use vswhere to find installation path
if exist "!VSWHERE!" (
    for /f "usebackq tokens=*" %%i in (`"!VSWHERE!" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do (
        set "VS_PATH=%%i"
        set "NEED_CPP=0"
    )
)

if "!NEED_CPP!"=="1" (
    echo    - C++ Build Tools not detected.
    echo    - Downloading and installing Visual C++ Build Tools + Windows SDK...
    echo    - This may take a while ^(1-2 GB download^). Please wait...
    
    REM Download vs_buildtools.exe
    powershell -Command "Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vs_buildtools.exe' -OutFile 'vs_buildtools.exe'"
    
    REM Install silently with VCTools AND Windows 10 SDK
    start /wait vs_buildtools.exe --passive --wait --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.Windows10SDK.19041 --includeRecommended --norestart
    
    echo    - Visual C++ Build Tools installation finished.
    if exist vs_buildtools.exe del vs_buildtools.exe
    
    REM Try to find the path again after installation
    if exist "!VSWHERE!" (
        for /f "usebackq tokens=*" %%i in (`"!VSWHERE!" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do (
            set "VS_PATH=%%i"
        )
    )
) else (
    echo    - Visual C++ Build Tools are already installed at: !VS_PATH!
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
    
    REM Update PATH for current session manually
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
) else (
    echo    - Rust is already installed.
)

REM ---------------------------------------------------
REM 3. CHECK & INSTALL PYTHON 3.12 SPECIFICALLY
REM ---------------------------------------------------
echo.
echo [3/4] Checking Python 3.12...

set "PYTHON_CMD="

REM Check if py launcher exists and can find 3.12
py -3.12 --version >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py -3.12"
    echo    - Python 3.12 found via py launcher.
    goto :python_ready
)

REM Check for python3.12 in path
where python3.12 >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python3.12"
    echo    - Python 3.12 found in PATH.
    goto :python_ready
)

REM Check default python and verify version
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
echo !PY_VER! | findstr /b "3.12" >nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    echo    - Python 3.12 is the default python.
    goto :python_ready
)

REM Python 3.12 not found, install it
echo    - Python 3.12 not found. Downloading...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.1/python-3.12.1-amd64.exe' -OutFile 'python_installer.exe'"

echo    - Installing Python 3.12...
start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

echo    - Python 3.12 installed.
if exist python_installer.exe del python_installer.exe

REM After install, use py launcher
set "PYTHON_CMD=py -3.12"

:python_ready

REM ---------------------------------------------------
REM 4. SETUP VENV AND INSTALL DEPENDENCIES
REM ---------------------------------------------------
echo.
echo [4/4] Setting up Project Environment...

REM Activate C++ Build Tools Environment if found
if defined VS_PATH (
    if exist "!VS_PATH!\VC\Auxiliary\Build\vcvars64.bat" (
        echo    - Initializing Visual C++ Environment...
        call "!VS_PATH!\VC\Auxiliary\Build\vcvars64.bat" >nul
    )
)

REM Delete old venv if using wrong Python version
if exist venv (
    echo    - Checking existing venv Python version...
    venv\Scripts\python --version 2>nul | findstr "3.12" >nul
    if !errorlevel! neq 0 (
        echo    - Existing venv uses wrong Python version. Recreating...
        rmdir /s /q venv
    )
)

if not exist venv (
    echo    - Creating virtual environment with Python 3.12...
    !PYTHON_CMD! -m venv venv
) else (
    echo    - Virtual environment 'venv' already exists with correct Python.
)

echo    - Activating venv...
call venv\Scripts\activate

echo    - Upgrading pip...
python -m pip install --upgrade pip

echo    - Installing requirements...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install requirements!
    echo Please ensure Visual C++ Build Tools and Windows SDK are installed correctly.
    pause
    exit /b 1
)

REM Create .env from .env.example if it doesn't exist
if not exist .env (
    if exist .env.example (
        echo    - Creating .env from .env.example...
        copy .env.example .env >nul
        echo    - IMPORTANT: Please edit .env with your database credentials!
    ) else (
        echo [WARNING] No .env or .env.example found. App may not start correctly.
    )
) else (
    echo    - .env file already exists.
)

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
