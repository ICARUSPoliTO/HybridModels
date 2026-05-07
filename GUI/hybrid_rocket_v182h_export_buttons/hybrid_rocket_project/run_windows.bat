@echo off
REM =============================================================================
REM Hybrid Rocket Simulator - Setup and Run Script (Windows)
REM =============================================================================
REM This script will:
REM   1. Check Python installation
REM   2. Install required dependencies
REM   3. Launch the GUI
REM =============================================================================

echo.
echo ============================================
echo   Hybrid Rocket Simulator - Setup
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not available!
    echo Please ensure pip is installed with Python.
    pause
    exit /b 1
)

echo [OK] pip found
echo.

REM Install dependencies
echo Installing dependencies...
echo.
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [WARNING] Some packages may have failed to install.
    echo If RocketCEA failed, you may need to install Visual Studio Build Tools.
    echo.
    pause
)

echo.
echo ============================================
echo   Starting Hybrid Rocket Simulator...
echo ============================================
echo.

REM Run the application
python main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application crashed or failed to start.
    echo Check the error messages above.
    pause
)
