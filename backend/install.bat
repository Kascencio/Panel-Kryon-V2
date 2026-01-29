@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo      PANEL KRYON - INSTALLATION START
echo ===================================================

cd /d "%~dp0"

:: ---------------------------------------------------
:: 1. CHECK & INSTALL VISUAL C++ BUILD TOOLS
:: ---------------------------------------------------
echo.
echo [1/4] Checking Visual C++ Build Tools...

where cl >nul 2>nul
if %errorlevel% neq 0 (
    echo    - C++ Compiler ^(cl.exe^) not found.
    echo    - Downloading and installing Visual C++ Build Tools...
    echo    - This may take a while. Please wait...
    
    :: Download vs_buildtools.exe
    powershell -Command "Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vs_buildtools.exe' -OutFile 'vs_buildtools.exe'"
    
    :: Install silently
    start /wait vs_buildtools.exe --passive --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --norestart
    
    echo    - Visual C++ Build Tools installed.
    del vs_buildtools.exe
) else (
    echo    - Visual C++ Build Tools are already installed.
)

:: ---------------------------------------------------
:: 2. CHECK & INSTALL RUST & CARGO
:: ---------------------------------------------------
echo.
echo [2/4] Checking Rust and Cargo...

where cargo >nul 2>nul
if %errorlevel% neq 0 (
    echo    - Cargo/Rust not found.
    echo    - Downloading Rustup...
    
    :: Download rustup
    powershell -Command "Invoke-WebRequest -Uri 'https://win.rustup.rs/x86_64' -OutFile 'rustup-init.exe'"
    
    :: Install silently
    echo    - Installing Rust...
    start /wait rustup-init.exe -y
    
    echo    - Rust installed.
    del rustup-init.exe
    
    :: Update PATH for current session
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
) else (
    echo    - Rust is already installed.
)

:: ---------------------------------------------------
:: 3. CHECK & INSTALL PYTHON
:: ---------------------------------------------------
echo.
echo [3/4] Checking Python...

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo    - Python not found.
    echo    - Downloading Python 3.12 installer...
    
    :: Download Python installer
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.1/python-3.12.1-amd64.exe' -OutFile 'python_installer.exe'"
    
    :: Install silently
    echo    - Installing Python...
    start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    echo    - Python installed.
    del python_installer.exe
    
    :: Refresh env vars is tricky in batch, asking user to potentially restart if things fail implies a restart might be needed, 
    :: but we try to proceed using default path if possible or re-checking.
    :: For now, we assume it's in path or we use py launcher if available.
) else (
    echo    - Python is already installed.
)

:: ---------------------------------------------------
:: 4. SETUP VENV AND INSTALL DEPENDENCIES
:: ---------------------------------------------------
echo.
echo [4/4] Setting up Project Environment...

:: Check if python is available now
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

:: Optional: Initialize DB
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
