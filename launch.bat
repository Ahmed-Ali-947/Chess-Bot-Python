@echo off
echo ================================================
echo   Chess AI - Windows Launcher
echo ================================================

:: Check if Python is installed
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python not found. Download from https://python.org
    pause
    exit /b 1
)

:: Install dependencies
echo Installing dependencies...
python -m pip install -r requirements.txt --quiet

:: Launch game
echo Launching Chess AI...
python run.py

pause
