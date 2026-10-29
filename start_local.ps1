# AI QA Agent Local Launcher (PowerShell)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       AI QA AGENT - AUTONOMOUS QA SAAS PLATFORM          " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$root = $PSScriptRoot

Write-Host "`n[1/3] Starting Backend API Server (Uvicorn / FastAPI on :8000)..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList "/k", "$root\run_backend.bat"

Write-Host "[2/3] Starting Frontend Web App (Next.js on :3000)..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList "/k", "$root\run_frontend.bat"

Write-Host "`n[3/3] Waiting for services to initialize..." -ForegroundColor Green
Start-Sleep -Seconds 4

Write-Host @"
==========================================================
Services are running:
  - Web Dashboard : http://localhost:3000
  - Swagger API   : http://127.0.0.1:8000/docs
  - Health Check  : http://127.0.0.1:8000/api/v1/healthz

Demo Account:
  Email    : architect@acme-qa.com
  Password : SecurePass123!
==========================================================
"@ -ForegroundColor Magenta

Start-Process "http://localhost:3000"
