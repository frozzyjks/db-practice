import pytest
import pytest_asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import delete
from sqlalchemy.pool import NullPool
from src.task3.main import app
from src.task3.database import Base, get_db
from src.task3.config import settings
from src.task3.models import SpimexTradingResults
from src.task3.cache import get_redis

DATABASE_URL = f"postgresql+asyncpg://{settings.db_user}:{settings.db_pass}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db() -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_db(setup_db: None) -> AsyncGenerator[None, None]:
    async with SessionLocal() as session:
        await session.execute(delete(SpimexTradingResults))
        await session.commit()
    yield



@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def mock_redis() -> AsyncGenerator[AsyncMock, None]:
    mock = AsyncMock()
    mock.get.return_value = None
    mock.setex.return_value = True

    app.dependency_overrides[get_redis] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_redis, None)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)