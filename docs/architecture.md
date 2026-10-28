# AI QA Agent — System Architecture

## 1. Overview
AI QA Agent is an enterprise-grade multi-tenant QA Automation and Intelligence SaaS platform. It discovers web applications, generates structured test cases using LLM agents, executes real Playwright test suites in isolated sandbox environments, records irrefutable step-by-step evidence (screenshots, network logs, console traces), detects bugs with root cause analysis, and assists with self-healing locators.

## 2. Core Architectural Pillars
- **Strict Separation of Concerns**: AI-generated suggestions are strictly separated from executed, verified test results. A test is NEVER marked `PASSED` without actual browser execution evidence.
- **Multi-Tenant Isolation**: Multi-tenancy is enforced at the organization boundary across API, database queries, and object storage paths.
- **Asynchronous Task Execution**: Heavy workloads (web crawling, AI generation, Playwright test runs) are offloaded to asynchronous workers via Redis/task queues with immediate task ID response (`202 Accepted`).
- **Zero-Trust Network & Security**: Target URL validation enforces strict SSRF protection (loopback/private IP banning, DNS rebinding validation, egress filtering).

## 3. High-Level Component Diagram
```mermaid
flowchart TD
    User([User / Browser]) <--> WebApp[Next.js App Router (apps/web)]
    WebApp <--> ApiGateway[FastAPI REST API (services/api)]
    
    subgraph Data Layer
        Postgres[(PostgreSQL 16)]
        Redis[(Redis Task Queue & Cache)]
        S3[(MinIO / S3 Object Storage)]
    end
    
    ApiGateway <--> Postgres
    ApiGateway <--> Redis
    
    subgraph Execution & Worker Layer
        Worker[Celery / Async Worker (services/worker)]
        PlaywrightRunner[Isolated Playwright Browser Sandbox]
        AIAdapter[AI Provider Adapter (OpenAI / Anthropic / Gemini)]
    end
    
    Worker <--> Redis
    Worker <--> Postgres
    Worker --> PlaywrightRunner
    Worker --> AIAdapter
    Worker --> S3
    
    subgraph Target Applications
        TargetWeb[Target Web Application (Under Test)]
        TargetRepo[GitHub Repository (Read-only Analysis)]
    end
    
    PlaywrightRunner --> TargetWeb
    Worker --> TargetRepo
```

## 4. Subsystem Breakdown

### 4.1. Web Application (`apps/web`)
- **Framework**: Next.js 14+ App Router, TypeScript (strict mode), Tailwind CSS, shadcn/ui components.
- **Theme**: Dark purple base (`#0f0c1b`, `#1a162b`) with measured vibrant orange accents (`#ff6b00`, `#ff8533`).
- **Responsibilities**:
  - Dashboard with real KPI counters (no fake fixed stats).
  - Project Creation Wizard with URL and GitHub validation.
  - Project Intelligence (discovered pages, forms, endpoints, observed vs inferred tags).
  - Test Case Studio (manual and automated test case management, versioning, export).
  - Execution Center (real-time run progress, step-by-step screenshot carousel, logs).
  - Bug Intelligence (actionable bug cards linked to test runs).
  - Automation Lab & Workspace Settings.

### 4.2. API Service (`services/api`)
- **Framework**: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, Alembic.
- **Key Layers**:
  - `api/v1`: REST endpoints with OpenAPI specs.
  - `core`: Security, JWT auth, RBAC permissions, config, SSRF validator.
  - `models`: Relational database models (PostgreSQL).
  - `schemas`: Strict request/response validation schemas.
  - `services`: Business logic (Project, TestRun, Discovery, AI, Billing).
  - `integrations`: GitHub client, S3 client, AI client adapters.

### 4.3. Worker & Execution Service (`services/worker`)
- **Engine**: Playwright Python in headless isolated containers.
- **Tasks**:
  - `discover_project_url`: SSRF-safe page crawler extracting accessible roles, forms, inputs, links.
  - `generate_test_cases`: AI schema-validated prompt processing.
  - `execute_test_run`: Isolated browser sandbox execution, step timers, artifact capture.
  - `investigate_failure`: Auto-capture DOM snapshot upon failure for root cause triage.

### 4.4. Packages & Schemas
- `packages/shared-types`: Canonical TypeScript definitions mirrored from backend schemas.
- `packages/test-schema`: Canonical JSON Schema and Pydantic models for test cases, step actions, assertions, and execution results.
