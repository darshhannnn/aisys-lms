@echo off
REM AISYS LMS Offline Installation Script for Windows
REM This script installs the system without requiring internet access

echo ========================================
echo AISYS LMS Offline Installation
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11+ and add it to PATH
    pause
    exit /b 1
)

echo [OK] Python found
python --version

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv .venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

echo [OK] Virtual environment created

REM Activate virtual environment
echo.
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies from local wheels or bundled packages
echo.
echo Installing dependencies...
pip install -e "."
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [OK] Dependencies installed

REM Copy environment configuration
echo.
echo Setting up environment configuration...
if not exist .env (
    copy .env.example .env
    echo [OK] .env file created from .env.example
) else (
    echo [OK] .env file already exists
)

REM Run database migrations
echo.
echo Running database migrations...
python -m alembic upgrade head
if %errorlevel% neq 0 (
    echo [ERROR] Failed to run migrations
    pause
    exit /b 1
)

echo [OK] Database migrations completed

REM Seed initial data (optional)
echo.
echo Would you like to seed initial data? (Y/N)
set /p seed_choice=
if /i "%seed_choice%"=="Y" (
    echo Seeding initial data...
    aisys seed all
    echo [OK] Initial data seeded
)

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo To start the application:
echo   1. Activate virtual environment: .venv\Scripts\activate.bat
echo   2. Start server: uvicorn app.main:app --host 0.0.0.0 --port 8000
echo   3. Open browser: http://localhost:8000
echo.
pause
