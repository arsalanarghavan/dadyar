@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

title دادیار هوشمند

:: Check for Python (try py launcher first, then python)
set PYEXE=
where py >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('py -3 -c "import sys; print(sys.executable)" 2nul') do set PYEXE=%%i
)
if not defined PYEXE (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "delims=" %%i in ('python -c "import sys; print(sys.executable)" 2nul') do set PYEXE=%%i
    )
)

if not defined PYEXE (
    echo.
    echo [خطا] پایتون یافت نشد.
    echo لطفاً پایتون 3.10 یا بالاتر را از https://www.python.org/downloads/ نصب کنید.
    echo هنگام نصب گزینه "Add Python to PATH" را فعال کنید.
    echo.
    pause
    exit /b 1
)

echo پایتون: %PYEXE%
echo.

:: Create venv if missing
if not exist "venv\Scripts\python.exe" (
    echo در حال ایجاد محیط مجازی...
    "%PYEXE%" -m venv venv
    if errorlevel 1 (
        echo [خطا] ایجاد venv ناموفق بود.
        pause
        exit /b 1
    )
    echo محیط مجازی ایجاد شد.
    echo.
)

:: Install dependencies if needed (quick check: streamlit in venv)
venv\Scripts\python.exe -c "import streamlit" 2>nul
if errorlevel 1 (
    echo در حال نصب کتابخانه‌ها...
    venv\Scripts\pip install -q -r requirements.txt
    if errorlevel 1 (
        echo [خطا] نصب وابستگی‌ها ناموفق بود.
        pause
        exit /b 1
    )
    echo نصب کتابخانه‌ها انجام شد.
    echo.
) else (
    echo وابستگی‌ها از قبل نصب شده‌اند.
    echo.
)

:: Copy .env from example if missing
if not exist ".env" (
    if exist ".env.example" (
        copy /y ".env.example" ".env" >nul
        echo فایل .env از .env.example ساخته شد.
        echo لطفاً کلید API را در فایل .env تنظیم کنید.
        echo.
    )
)

:: Run the app
echo در حال اجرای دادیار هوشمند...
echo برای خروج Ctrl+C بزنید.
echo.
venv\Scripts\python.exe launcher.py

pause
