@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>nul
cd /d "%~dp0"

title دادیار هوشمند

echo.
echo ════════════════════════════════════════════════════════
echo           دادیار هوشمند
echo ════════════════════════════════════════════════════════
echo.

if not exist "venv\Scripts\python.exe" (
    echo [X] خطا: محیط مجازی یافت نشد
    echo.
    echo لطفاً ابتدا installer.bat را اجرا کنید
    echo.
    pause
    exit /b 1
)

if not exist "launcher.py" (
    echo [X] خطا: فایل launcher.py یافت نشد
    echo.
    pause
    exit /b 1
)

echo [√] محیط آماده است. برنامه شروع می‌شود...
echo.

venv\Scripts\python.exe launcher.py

echo.
pause
endlocal
exit /b 0
