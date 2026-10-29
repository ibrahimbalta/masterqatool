from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from services.api.app.db.session import get_db

router = APIRouter(tags=["Health & Probes"])

@router.get("/health", status_code=status.HTTP_200_OK)
@router.get("/healthz", status_code=status.HTTP_200_OK)
async def healthz():
    return {"status": "ok", "service": "ai-qa-agent-api"}

@router.get("/readyz", status_code=status.HTTP_200_OK)
async def readyz(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
