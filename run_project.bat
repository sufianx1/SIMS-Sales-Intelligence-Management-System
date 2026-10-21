@echo off
setlocal enabledelayedexpansion
title SIMS - Sales Intelligence and Management System Launcher
cd /d "%~dp0"

echo ==============================================================================
echo           SIMS - Sales Intelligence and Management System Launcher
echo ==============================================================================
echo.

:: 1. Check Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not found in your PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

:: 2. Check Node / npm
where npm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js / npm is not found in your PATH!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo [1/3] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "SIMS Backend (FastAPI)" cmd /c "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/3] Launching React Vite Frontend on http://localhost:5173 ...
start "SIMS Frontend (Vite)" cmd /c "cd /d "%~dp0frontend" && npm run dev"

echo [3/3] Waiting for servers to initialize...
timeout /t 4 /nobreak >nul

:: Open browser
start http://localhost:5173

echo.
echo ==============================================================================
echo                  SIMS IS RUNNING SUCCESSFULLY!
echo ==============================================================================
echo   Web Application:    http://localhost:5173
echo   Backend API:        http://127.0.0.1:8000
echo   API Documentation:  http://127.0.0.1:8000/docs
echo ==============================================================================
echo.
echo DEMO LOGIN CREDENTIALS (Password for all: Demo12345!)
echo ------------------------------------------------------------------------------
echo   Platform Super Admin : superadmin
echo   Superstore Admin     : superstore.admin
echo   Superstore Employee  : superstore.employee
echo   Nike Admin           : nike.admin
echo   Nike Employee        : nike.employee
echo   Puma Admin           : puma.admin
echo   Puma Employee        : puma.employee
echo ==============================================================================
echo.
echo Press any key to stop all SIMS servers and close this launcher...
pause >nul

echo Stopping SIMS servers...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000, 5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"

echo Servers stopped. Goodbye!
timeout /t 2 /nobreak >nul
