#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "    AI QA AGENT - CODESPACES AUTO SETUP & LAUNCHER        "
echo "=========================================================="

echo ""
echo "[1/4] Installing Python Backend dependencies..."
pip install -r requirements.txt

echo ""
echo "[2/4] Seeding Database with Demo Architecture Data..."
python scripts/seed_demo_data.py

echo ""
echo "[3/4] Starting FastAPI Backend on Port 8000 (background)..."
pkill -f "uvicorn services.api.app.main:app" || true
nohup python -m uvicorn services.api.app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
echo "Backend started in background (logs in backend.log)."

echo ""
echo "[4/4] Installing Frontend dependencies & launching Next.js on Port 3000..."
cd apps/web
npm install
npm run dev
