import logging
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
from services.api.app.api.v1.test_runs import router as test_run_router
from services.api.app.api.v1.bugs import router as bug_router
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
    allow_origins=settings.BACKEND_CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers under /api/v1
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(org_router, prefix="/api/v1")
app.include_router(project_router, prefix="/api/v1")
app.include_router(scan_router, prefix="/api/v1")
app.include_router(test_case_router, prefix="/api/v1")
app.include_router(test_run_router, prefix="/api/v1")
app.include_router(bug_router, prefix="/api/v1")
app.include_router(usage_router, prefix="/api/v1")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact system administrator."}
    )
