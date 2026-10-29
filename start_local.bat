@echo off
title AI QA Agent - Local Launcher
cd /d "%~dp0"

echo ==========================================================
echo        AI QA AGENT - AUTONOMOUS QA SAAS PLATFORM
echo ==========================================================
echo.
echo [1/3] Starting Backend API Server (Uvicorn / FastAPI on :8000)...
start "AI QA Agent Backend (:8000)" cmd /k "run_backend.bat"

echo [2/3] Starting Frontend Web App (Next.js on :3000)...
start "AI QA Agent Frontend (:3000)" cmd /k "run_frontend.bat"

echo.
echo [3/3] Waiting for services to initialize...
timeout /t 4 /nobreak >nul

echo.
echo ==========================================================
echo Services are running:
echo   - Web Dashboard : http://localhost:3000
echo   - Swagger API   : http://127.0.0.1:8000/docs
echo   - Health Check  : http://127.0.0.1:8000/api/v1/healthz
echo.
echo Demo Account:
echo   Email    : architect@acme-qa.com
echo   Password : SecurePass123!
echo ==========================================================
echo.
echo Opening browser...
start http://localhost:3000
