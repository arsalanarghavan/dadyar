@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>nul
cd /d "%~dp0"

title دادیار هوشمند - نصاب

cls
echo.
echo ════════════════════════════════════════════════════════
echo           دادیار هوشمند - نصاب و راه‌اندازی
echo ════════════════════════════════════════════════════════
echo.

:: ===== تنظیمات =====
set "PYTHON_URL=https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe"
set "PYTHON_INSTALLER=%TEMP%\python-installer.exe"
set "PYEXE="

:: ===== بررسی و بارگذاری معیارها =====
echo [*] بررسی معیارهای سیستم...

if not exist "launcher.py" (
    echo [X] خطا: فایل launcher.py یافت نشد
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo [X] خطا: فایل requirements.txt یافت نشد
    pause
    exit /b 1
)
echo [√] تمام فایل‌های پایه موجود هستند
echo.

:: ===== جستجوی Python =====
echo [*] جستجوی Python در سیستم...

:: روش 1: بررسی مسیرهای دایمی
set "PYTHON_PATHS=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
set "PYTHON_PATHS=!PYTHON_PATHS! %LOCALAPPDATA%\Programs\Python\Python312\python.exe"
set "PYTHON_PATHS=!PYTHON_PATHS! %LOCALAPPDATA%\Programs\Python\Python311\python.exe"
set "PYTHON_PATHS=!PYTHON_PATHS! %LOCALAPPDATA%\Programs\Python\Python310\python.exe"
set "PYTHON_PATHS=!PYTHON_PATHS! C:\Python313\python.exe C:\Python312\python.exe C:\Python311\python.exe C:\Python310\python.exe"

for %%P in (!PYTHON_PATHS!) do (
    if exist "%%P" (
        set "PYEXE=%%P"
        goto :python_found
    )
)

:: روش 2: بررسی PATH
where python >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%A in ('where python') do (
        set "PYEXE=%%A"
        goto :python_found
    )
)

:: روش 3: بررسی py launcher
where py >nul 2>&1
if not errorlevel 1 (
    set "PYEXE=py"
    goto :python_found
)

:python_not_found
echo [!] Python یافت نشد. درحال دانلود و نصب...
echo.

:: دانلود Python
echo [*] دانلود Python 3.13 (تقریباً 150 MB)...
powershell -NoProfile -Command "& {$ProgressPreference = 'SilentlyContinue'; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%' -TimeoutSec 300; Write-Host '[√] دانلود تکمیل شد'}"

if not exist "%PYTHON_INSTALLER%" (
    echo [X] خطا: دانلود ناموفق بود
    echo.
    echo لطفاً Python را دستی نصب کنید:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: نصب Python
echo [*] نصب Python (منتظر بمانید)...
"%PYTHON_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 >nul 2>&1
timeout /t 3 /nobreak >nul

:: بررسی نصب
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    echo [√] Python نصب شد
) else (
    echo [X] خطا در نصب Python
    del /q "%PYTHON_INSTALLER%" >nul 2>&1
    pause
    exit /b 1
)

:: پاک‌سازی
del /q "%PYTHON_INSTALLER%" >nul 2>&1
set "PATH=%LOCALAPPDATA%\Programs\Python\Python313;%LOCALAPPDATA%\Programs\Python\Python313\Scripts;%PATH%"

:python_found
echo [√] Python ready: !PYEXE!
echo.

:: ===== ایجاد محیط مجازی =====
echo [*] بررسی محیط مجازی...

if not exist "venv\Scripts\python.exe" (
    echo [*] ایجاد محیط مجازی (منتظر بمانید)...
    "!PYEXE!" -m venv venv
    
    if errorlevel 1 (
        echo [X] خطا در ایجاد محیط مجازی
        pause
        exit /b 1
    )
    echo [√] محیط مجازی ایجاد شد
) else (
    echo [√] محیط مجازی موجود است
)
echo.

:: ===== نصب وابستگی‌ها =====
echo [*] بروزرسانی pip...
venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel >nul 2>&1

echo [*] نصب وابستگی‌ها...
echo (منتظر بمانید - ممکن است 5-15 دقیقه طول بکشد)
echo.

venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo [!] هشدار: برخی وابستگی‌ها شاید کامل نصب نشده‌اند
    echo     دوباره تلاش کنید یا اتصال اینترنت را بررسی کنید
)
echo [√] نصب تکمیل شد
echo.

:: ===== تنظیم .env =====
if not exist ".env" (
    if exist ".env.example" (
        copy /y ".env.example" ".env" >nul
        echo [√] فایل .env ایجاد شد
    )
)
echo.

:: ===== شروع برنامه =====
echo ════════════════════════════════════════════════════════
echo           برنامه دادیار هوشمند شروع می‌شود...
echo ════════════════════════════════════════════════════════
echo.

venv\Scripts\python.exe launcher.py

echo.
echo [√] برنامه بسته شد
echo.
pause
endlocal
exit /b 0
