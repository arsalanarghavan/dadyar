@echo off
chcp 65001 >nul 2>&1
REM ══════════════════════════════════════════════════════════════════
REM  Dadyar – Judicial Decision-Making Simulator
REM  Installer ^& Launcher Script (Windows)
REM ══════════════════════════════════════════════════════════════════

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%\.."
set "VENV_DIR=%PROJECT_ROOT%\.venv"
set "REQUIREMENTS=%SCRIPT_DIR%requirements.txt"
set "ENV_FILE=%PROJECT_ROOT%\.env"
set "ENV_EXAMPLE=%PROJECT_ROOT%\.env.example"
set "APP_FILE=%SCRIPT_DIR%app.py"

echo ══════════════════════════════════════════════════════════════
echo   Dadyar – Judicial Decision-Making Simulator
echo ══════════════════════════════════════════════════════════════
echo.

REM ─── 1. Check Python ──────────────────────────────────────────
echo [1/5] Checking Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python 3.9+
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VERSION=%%v
echo OK: Python %PY_VERSION%

REM ─── 2. Create virtual environment ────────────────────────────
echo [2/5] Setting up virtual environment...
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    python -m venv "%VENV_DIR%"
    echo OK: Virtual environment created
) else (
    echo OK: Virtual environment already exists
)

call "%VENV_DIR%\Scripts\activate.bat"

REM ─── 3. Upgrade pip ───────────────────────────────────────────
echo [3/5] Upgrading pip...
pip install --upgrade pip setuptools wheel --quiet >nul 2>&1
echo OK: pip upgraded

REM ─── 4. Install dependencies ──────────────────────────────────
echo [4/5] Installing dependencies...
if not exist "%REQUIREMENTS%" (
    echo ERROR: requirements.txt not found!
    pause
    exit /b 1
)

pip install -r "%REQUIREMENTS%" --quiet
echo OK: All dependencies installed

REM ─── 5. Setup .env file ───────────────────────────────────────
echo [5/5] Checking configuration...
if not exist "%ENV_FILE%" (
    if exist "%ENV_EXAMPLE%" (
        copy "%ENV_EXAMPLE%" "%ENV_FILE%" >nul
        echo WARNING: Created .env from .env.example – please add your API key
        echo   Edit: %ENV_FILE%
    ) else (
        (
            echo AI_PROVIDER=gemini
            echo OPENAI_API_KEY=sk-your-api-key-here
            echo OPENAI_MODEL=gpt-4-turbo-preview
            echo OPENAI_TEMPERATURE=0.3
            echo OPENAI_MAX_TOKENS=2000
            echo EMBEDDING_MODEL=text-embedding-3-small
            echo EMBEDDING_DIMENSION=1536
            echo GEMINI_API_KEY=your-gemini-api-key-here
            echo GEMINI_MODEL=gemini-2.0-flash
            echo GEMINI_EMBEDDING_MODEL=models/text-embedding-004
            echo GEMINI_EMBEDDING_DIMENSION=768
        ) > "%ENV_FILE%"
        echo WARNING: Created default .env – please add your API key
    )
) else (
    echo OK: .env already configured
)

REM ─── Launch ────────────────────────────────────────────────────
echo.
echo ══════════════════════════════════════════════════════════════
echo   Setup complete! Launching the application...
echo ══════════════════════════════════════════════════════════════
echo.

cd /d "%SCRIPT_DIR%"
streamlit run "%APP_FILE%" --server.headless true

pause
