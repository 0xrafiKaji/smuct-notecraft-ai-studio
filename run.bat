@echo off
setlocal enabledelayedexpansion

echo ======================================================================
echo   Starting NoteCraft AI Studio (SMUCT Production Suite)
echo ======================================================================

:: Check Python installation
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    where py >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Python 3 is not found on your system!
        echo Please download and install Python from https://www.python.org/
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

:: Create virtual environment if it does not exist
if not exist "venv" (
    echo [INFO] Creating Python virtual environment (venv)...
    %PYTHON_CMD% -m venv venv
    call venv\Scripts\activate.bat
    echo [INFO] Installing required dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

:: Create .env if not exists
if not exist ".env" (
    echo [INFO] Creating .env file from .env.example...
    if exist ".env.example" (
        copy .env.example .env >nul
    ) else (
        echo GEMINI_API_KEY=>.env
        echo PORT=8000>>.env
        echo ADMIN_PASSWORD=rafik2026>>.env
        echo GOOGLE_SHEET_ID=1Dg4poYmMlhm6WDUl0XYwhgSR33BDsi7DjGCQOLqz0R0>>.env
    )
)

set PORT=8000

echo.
echo ======================================================================
echo   Status:
echo    - Environment: .env loaded
echo    - Google Sheet ID: 1Dg4poYmMlhm6WDUl0XYwhgSR33BDsi7DjGCQOLqz0R0
echo    - Local Web Server: http://localhost:%PORT%
echo    - API Docs: http://localhost:%PORT%/docs
echo.
echo   Opening NoteCraft Studio in your browser...
echo   Press Ctrl+C in this window to stop the server.
echo ======================================================================

start http://localhost:%PORT%
python -m uvicorn backend.main:app --host 0.0.0.0 --port %PORT% --reload

pause
