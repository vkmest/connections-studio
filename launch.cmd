@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo First-time setup is needed. In this folder, run:
    echo   py -3 -m venv .venv
    echo   .venv\Scripts\python -m pip install -e ".[desktop]"
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -c "import connections, PySide6.QtWidgets" >nul 2>&1
if errorlevel 1 (
    echo Desktop dependencies are missing. Run:
    echo   .venv\Scripts\python -m pip install -e ".[desktop]"
    pause
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" -m connections gui
