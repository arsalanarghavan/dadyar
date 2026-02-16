@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

title ساخت نسخه ویندوز — دادیار هوشمند

:: Require venv (run install_and_run.bat once first, or create venv manually)
if not exist "venv\Scripts\activate.bat" (
    echo [خطا] ابتدا install_and_run.bat را یک بار اجرا کنید تا venv و وابستگی‌ها نصب شوند.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo نصب PyInstaller...
pip install -q pyinstaller
if errorlevel 1 (
    echo [خطا] نصب PyInstaller ناموفق بود.
    pause
    exit /b 1
)

echo.
echo در حال ساخت با PyInstaller...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller dadyar.spec --noconfirm
if errorlevel 1 (
    echo [خطا] ساخت ناموفق بود.
    pause
    exit /b 1
)

if exist "dist\dadyar\dadyar.exe" (
    echo.
    echo ساخت با موفقیت انجام شد.
    echo خروجی: dist\dadyar\
    echo برای توزیع، پوشه dist\dadyar را به‌صورت zip منتشر کنید.
    echo.
) else (
    echo [خطا] فایل exe ساخته نشد.
    exit /b 1
)

pause
