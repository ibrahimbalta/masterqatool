@echo off
title AI QA Agent - Backend API (Port 8000)
cd /d "%~dp0"
echo ===================================================
echo   Starting AI QA Agent Backend API on Port 8000...
echo ===================================================
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] .venv not found, using system Python...
)
python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000 --reload
pause
