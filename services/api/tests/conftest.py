import os
import pytest
from typing import AsyncGenerator

# Enforce in-memory SQLite during pytest runs before any model or DB import
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_qa_agent.db"

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from services.api.app.main import app
from services.api.app.db.session import Base, get_db, engine as app_engine
import services.api.app.models  # noqa: F401

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with app_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c

    async with app_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
