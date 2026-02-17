@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

title دادیار هوشمند

:: Check for Python (try py launcher first, then python, then check common paths)
set PYEXE=

:: Try py launcher (Windows Python launcher)
py -3 --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYEXE=py -3
    goto :pythonFound
)

:: Try python command
python --version >nul 2>&1
if !errorlevel! equ 0 (
    set PYEXE=python
    goto :pythonFound
)

:: Try common installation paths
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python314\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist "%%P" (
        set PYEXE=%%P
        goto :pythonFound
    )
)

:pythonNotFound
echo.
echo [خطا] پایتون یافت نشد.
echo لطفاً پایتون 3.10 یا بالاتر را از https://www.python.org/downloads/ نصب کنید.
echo هنگام نصب گزینه "Add Python to PATH" را حتماً فعال کنید.
echo.
pause
exit /b 1

:pythonFound
echo Python یافت شد: %PYEXE%
echo.

:: Create venv if missing
if not exist "venv\Scripts\python.exe" (
    echo در حال ایجاد محیط مجازی...
    "%PYEXE%" -m venv venv
    if !errorlevel! equ 1 (
        echo [خطا] ایجاد venv ناموفق بود.
        pause
        exit /b 1
    )
    echo محیط مجازی ایجاد شد.
    echo.
)

:: Install dependencies if needed (quick check: streamlit in venv)
venv\Scripts\python.exe -c "import streamlit" 2>nul
if !errorlevel! equ 1 (
    echo در حال نصب کتابخانه‌ها...
    echo (این ممکنه چند دقیقه زمان ببره)
    venv\Scripts\pip install -r requirements.txt
    if !errorlevel! equ 1 (
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
