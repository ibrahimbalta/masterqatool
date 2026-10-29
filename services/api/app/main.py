import logging
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.api.app.core.config import settings
from services.api.app.db.session import engine, Base
import services.api.app.models  # Register all models with Base.metadata

from services.api.app.api.v1.auth import router as auth_router
from services.api.app.api.v1.organizations import router as org_router
from services.api.app.api.v1.projects import router as project_router
from services.api.app.api.v1.scans import router as scan_router
from services.api.app.api.v1.test_cases import router as test_case_router
from services.api.app.api.v1.test_suites import router as test_suite_router
from services.api.app.api.v1.test_runs import router as test_run_router
from services.api.app.api.v1.bugs import router as bug_router
from services.api.app.api.v1.automation import router as automation_router
from services.api.app.api.v1.integrations import router as integration_router
from services.api.app.api.v1.artifacts import router as artifact_router
from services.api.app.api.v1.usage import router as usage_router
from services.api.app.api.v1.health import router as health_router

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("ai_qa_agent")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AI QA Agent API...")
    # Initialize DB schema for dev / SQLite testing
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schemas verified.")
    try:
        from scripts.seed_demo_data import seed
        await seed()
        logger.info("Initial seed data verified.")
    except Exception as e:
        logger.warning(f"Auto-seed skipped: {e}")
    yield
    logger.info("Shutting down AI QA Agent API...")
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Enterprise-grade AI-powered QA Automation & Intelligence SaaS API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = req_id
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Response-Time-Ms"] = f"{process_time:.2f}"

    if request.url.path not in ["/health", "/docs", "/openapi.json"]:
        logger.info(f"[{req_id[:8]}] {request.method} {request.url.path} -> {response.status_code} ({process_time:.1f}ms)")

    return response

# API Routers under /api/v1
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(org_router, prefix="/api/v1")
app.include_router(project_router, prefix="/api/v1")
app.include_router(scan_router, prefix="/api/v1")
app.include_router(test_case_router, prefix="/api/v1")
app.include_router(test_suite_router, prefix="/api/v1")
app.include_router(test_run_router, prefix="/api/v1")
app.include_router(bug_router, prefix="/api/v1")
app.include_router(automation_router, prefix="/api/v1")
app.include_router(integration_router, prefix="/api/v1")
app.include_router(artifact_router, prefix="/api/v1")
app.include_router(usage_router, prefix="/api/v1")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact system administrator."}
    )
