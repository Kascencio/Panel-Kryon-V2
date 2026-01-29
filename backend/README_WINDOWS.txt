-------------------------------------------------------------------------
           PANEL KRYON - WINDOWS INSTALLATION GUIDE
-------------------------------------------------------------------------

REQUIREMENTS:
- Internet connection (for downloading dependencies)
- Windows 10 or 11 recommended

-------------------------------------------------------------------------
1. AUTO-INSTALLATION
-------------------------------------------------------------------------
Just double-click on the file:
   
   install.bat

This script will automatically:
- Check if you have Visual C++ Build Tools (Required). If not, it installs them.
- Check if you have Rust & Cargo (Required). If not, it installs them.
- Check if you have Python 3.12. If not, it installs it.
- Create a virtual environment for the project.
- Install all necessary Python libraries.
- Initialize the database.

NOTE: If installers (Python, VS Build Tools, Rust) run, you might need to accept warnings
or wait for them to complete. If the script asks you to restart, please restart and run 'install.bat' again.

-------------------------------------------------------------------------
2. RUNNING THE APP
-------------------------------------------------------------------------
Once installation is complete, double-click:

   run.bat

This will:
- Start the server on http://localhost:8000
- Automatically open your default web browser to the app.

-------------------------------------------------------------------------
TROUBLESHOOTING
-------------------------------------------------------------------------
- If 'install.bat' fails to install Python or Rust automatically, please install them manually:
  * Python: https://www.python.org/downloads/
  * Rust: https://rustup.rs/
  * C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/ (Select "Desktop development with C++")

- If 'run.bat' closes immediately, try running it from a generic Command Prompt (cmd.exe)
  to see the error message.
