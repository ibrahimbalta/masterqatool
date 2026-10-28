# AI QA Agent — Development & Operational Guide

## Prerequisites
- **Node.js**: v20+ (v24 tested)
- **Python**: 3.11+ (3.12 tested)
- **PostgreSQL**: 15+ (or SQLite for fast isolated testing)
- **Redis**: 7+ (for asynchronous task broker)
- **Docker & Docker Compose** (for containerized stack)

## Quick Start (Local Development)

### 1. Environment Configuration
Copy the example environment file and set local secrets:
```bash
cp .env.example .env
```

### 2. Backend API Setup
```bash
# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\Activate.ps1
# On Unix:
source .venv/bin/activate

# Install dependencies
pip install -r services/api/requirements.txt

# Run migrations
alembic upgrade head

# Start API server
uvicorn services.api.app.main:app --reload --port 8000
```
API Documentation will be available at `http://localhost:8000/docs`.

### 3. Frontend Web Setup
```bash
cd apps/web
npm install
npm run dev
```
Frontend web application will run at `http://localhost:3000`.

### 4. Running Tests
```bash
# Backend unit & integration tests
pytest services/api/tests -v

# Frontend unit & component tests
cd apps/web && npm test
```

### 5. Dockerized Deployment
```bash
docker-compose up --build -d
```
Services exposed:
- `http://localhost:3000` — Next.js Dashboard
- `http://localhost:8000` — FastAPI Gateway & OpenAPI Docs
- `http://localhost:9000` — MinIO Object Storage Console
