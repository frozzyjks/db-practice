import pytest
import pytest_asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import delete
from sqlalchemy.pool import NullPool
from src.task3.main import app
from src.task3.database import Base, get_db, DATABASE_URL
from src.task3.config import settings
from src.task3.models import SpimexTradingResults
from src.task3.cache import get_redis
from src.task3.router import get_repository

engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db() -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_db(setup_db: None) -> AsyncGenerator[None, None]:
    async with AsyncSessionFactory() as session:
        await session.execute(delete(SpimexTradingResults))
        await session.commit()
    yield



@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
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
async def mock_repo() -> AsyncGenerator[AsyncMock, None]:
    mock = AsyncMock()

    mock.get_last_trading_dates.return_value = []
    mock.get_dynamics.return_value = []
    mock.get_trading_results.return_value = []

    app.dependency_overrides[get_repository] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_repository, None)


@pytest_asyncio.fixture
async def client(mock_redis: AsyncMock, mock_repo: AsyncMock) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac