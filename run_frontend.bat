@echo off
title AI QA Agent - Frontend Web App (Port 3000)
cd /d "%~dp0apps\web"
echo ===================================================
echo   Starting AI QA Agent Next.js UI on Port 3000...
echo ===================================================
npm run dev
pause
