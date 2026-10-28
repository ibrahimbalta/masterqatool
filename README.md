# AI QA Agent — Multi-Tenant Autonomous QA SaaS Platform

AI QA Agent is an enterprise-grade SaaS platform designed for autonomous web discovery, AI-assisted manual and automated test case design, isolated Playwright execution, evidence recording, and root-cause bug intelligence.

---

## Key Core Principles

1. **True Verification Principle**: An AI-generated test scenario is strictly decoupled from an executed, verified test result. A test result is NEVER marked as `PASSED` without actual browser execution traces and step-by-step evidence.
2. **Multi-Tenant Isolation**: Tenant boundaries are enforced via `organization_id` on every query, model, and API endpoint. Cross-tenant access is prohibited and verified by regression test suites.
3. **Zero-Trust Network & SSRF Defense**: All target URLs undergo strict scheme and DNS resolution checks to block access to loopbacks (`127.0.0.1`), private networks (`RFC 1918`), and cloud instance metadata services (`169.254.169.254`).
4. **No Fake Metrics**: Unmeasured KPIs (such as test coverage or artificial success metrics) are marked as *"Henüz hesaplanmadı"* until genuine DOM discovery and execution coverage are measured.

---

## Monorepo Architecture

```
ai-qa-agent/
  apps/
    web/                  # Next.js 14 App Router, TypeScript strict, Tailwind CSS
      app/                # App router pages (Dashboard, Projects, Execution, Studio, Bugs, Usage)
      components/         # Accessible, dark purple & orange UI components
      lib/api.ts          # Typed API client connected to backend
  services/
    api/                  # FastAPI REST API Gateway & Business Layer
      app/
        api/v1/           # Modular endpoints (Auth, Projects, Cases, Runs, Bugs, Usage, Health)
        core/             # Security (bcrypt, JWT), Config, SSRF Validator
        db/               # SQLAlchemy async engine & session management
        models/           # Comprehensive relational data models
        schemas/          # Strict Pydantic v2 validation models
        security/         # RBAC dependencies (Owner, Admin, Member, Viewer)
      migrations/         # Alembic database migrations
      tests/              # Async Pytest unit, multi-tenancy & security test suite
    worker/               # Playwright browser execution engine & task queue
  packages/
    shared-types/         # Shared TypeScript definitions
    test-schema/          # Canonical Pydantic test case schemas
  infrastructure/
    docker/               # Dockerfiles for API, Worker, and Web
  docs/
    architecture.md       # Full architectural design specification
    data-model.md         # Database entities, relationships & constraints
    security.md           # SSRF defense, sandboxing, and token protection
    development.md        # Local environment & deployment guide
  docker-compose.yml      # Orchestration for PostgreSQL, Redis, MinIO, API, Worker, Web
  .env.example            # Canonical environment variable specification
  pytest.ini              # Pytest configuration
  README.md
```

---

## Quick Start (Local Development)

### Prerequisites
- Node.js 20+ (v24 tested)
- Python 3.11+ (3.12 tested)

### 1. Configure Environment
```bash
cp .env.example .env
```

### 2. Run Backend API & Run Tests
```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1    # On Windows
# source .venv/bin/activate   # On Linux/macOS

# Install dependencies
pip install -r services/api/requirements.txt

# Run full test suite (Auth, SSRF, Multi-tenancy, Projects, Cases, Runs, Bugs)
pytest services/api/tests -v

# Start FastAPI Gateway
uvicorn services.api.app.main:app --reload --port 8000
```
OpenAPI documentation is available at `http://localhost:8000/docs`.

### 3. Run Frontend Web App
```bash
cd apps/web
npm install
npm run dev
```
Open `http://localhost:3000` to view the QA Intelligence Dashboard.

---

## Automated Verification Suite

Run the backend tests:
```bash
pytest services/api/tests -v
```
Verified Test Coverage:
- `test_user_registration_and_login` - User registration, password hashing, JWT issue, profile fetch.
- `test_duplicate_registration_fails` - Duplicate email detection and safe 400 rejection.
- `test_tenant_data_isolation` - Tenant A creates projects; Tenant B cannot read or patch them (HTTP 404), proving multi-tenant isolation.
- `test_project_and_test_case_lifecycle` - Project creation, test case versioning (v1 -> v2 on spec update), and CSV export.
- `test_test_run_execution_and_bug_tracking` - 202 Accepted run queueing, status checking, run cancellation, and bug dossier tracking.
- `test_ssrf_loopback_blocked` - Rejection of localhost, 127.0.0.1, [::1].
- `test_ssrf_cloud_metadata_blocked` - Rejection of AWS/GCP/Azure instance metadata endpoints (`169.254.169.254`, `metadata.google.internal`).
- `test_ssrf_scheme_restrictions` - Rejection of `file:`, `ftp:`, `gopher:`, `data:` schemes.
- `test_ssrf_legitimate_url_allowed` - Validation of valid external HTTP/HTTPS targets.

---

## Roadmap

- [x] **Phase 1**: Monorepo skeleton, Docker Compose, Database Models, Multi-tenancy, Auth & RBAC, Base UI & Dashboard, SSRF Protection, Comprehensive Automated Tests.
- [ ] **Phase 2**: URL Discovery Engine, recursive sitemap and DOM crawler, accessibility tree extraction, Project Intelligence view.
- [ ] **Phase 3**: AI Test Designer (LLM structured scenario generation, risk scoring, edge cases).
- [ ] **Phase 4**: Celery/Redis worker, isolated Playwright execution container, screenshot/trace artifact store.
- [ ] **Phase 5**: GitHub App integration, code analysis, regression suite selection, self-healing locators.
- [ ] **Phase 6**: Stripe/LemonSqueezy billing webhooks, concurrency throttles, audit log streaming.
