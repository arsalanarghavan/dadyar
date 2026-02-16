@echo off
REM ──────────────────────────────────────────────
REM Build script for دادیار هوشمند (Windows)
REM ──────────────────────────────────────────────
REM
REM Prerequisites:
REM   1. Python 3.12 installed
REM   2. Run from project root (where app.py is)
REM   3. Internet connection for first-time setup
REM ──────────────────────────────────────────────

echo.
echo Building dadyar hooshmand ...
echo.

REM Create venv if not exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt -q 2>nul
pip install pyinstaller -q 2>nul

REM Clean previous build
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Build
echo.
echo Running PyInstaller...
pyinstaller dadyar.spec --noconfirm

REM Check result
if exist "dist\dadyar\dadyar.exe" (
    echo.
    echo =============================================
    echo   Build successful!
    echo   Output: dist\dadyar\
    echo.
    echo   To run: dist\dadyar\dadyar.exe
    echo   To distribute: zip the dist\dadyar\ folder
    echo =============================================
) else (
    echo.
    echo Build failed!
    exit /b 1
)

pause
