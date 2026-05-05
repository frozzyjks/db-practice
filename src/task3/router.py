from datetime import date
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
from src.task3.cache import get_cached, get_redis, set_cached
from src.task3.database import get_db
from src.task3.repository import TradingRepository
from src.task3.schemas import TradingResult

router = APIRouter(prefix="/trading", tags=["Trading"])


def get_repository(
    db: AsyncSession = Depends(get_db),
) -> TradingRepository:
    return TradingRepository(db)


async def cached_response(
    redis: aioredis.Redis,
    cache_key: str,
    fetch_data,
    response_key: str = "data",
) -> dict[str, Any]:
    cached = await get_cached(redis, cache_key)
    if cached is not None:
        return {response_key: cached, "source": "cache"}

    data = await fetch_data()

    await set_cached(redis, cache_key, data)

    return {response_key: data, "source": "db"}


@router.get("/last-dates")
async def last_trading_dates(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Количество последних торговых дней",
    ),
    repo: TradingRepository = Depends(get_repository),
    redis: aioredis.Redis = Depends(get_redis),
) -> dict[str, Any]:
    cache_key = f"last_dates:{limit}"

    async def fetch() -> list[str]:
        dates = await repo.get_last_trading_dates(limit)
        return [str(d) for d in dates]

    return await cached_response(redis, cache_key, fetch, response_key="dates")


@router.get("/dynamics")
async def dynamics(
    start_date: date = Query(description="Начало периода (YYYY-MM-DD)"),
    end_date: date = Query(description="Конец периода (YYYY-MM-DD)"),
    oil_id: Optional[str] = Query(default=None, description="Код нефтепродукта (4 символа)"),
    delivery_type_id: Optional[str] = Query(default=None, description="Тип поставки (1 символ)"),
    delivery_basis_id: Optional[str] = Query(default=None, description="Базис поставки (3 символа)"),
    repo: TradingRepository = Depends(get_repository),
    redis: aioredis.Redis = Depends(get_redis),
) -> dict[str, Any]:
    cache_key = (
        f"dynamics:{start_date}:{end_date}"
        f":{oil_id}:{delivery_type_id}:{delivery_basis_id}"
    )

    async def fetch() -> list[dict]:
        trades = await repo.get_dynamics(
            start_date, end_date, oil_id, delivery_type_id, delivery_basis_id
        )
        return [TradingResult.model_validate(t).model_dump(mode="json") for t in trades]

    return await cached_response(redis, cache_key, fetch)


@router.get("/results")
async def trading_results(
    oil_id: Optional[str] = Query(default=None, description="Код нефтепродукта"),
    delivery_type_id: Optional[str] = Query(default=None, description="Тип поставки"),
    delivery_basis_id: Optional[str] = Query(default=None, description="Базис поставки"),
    limit: int = Query(default=10, ge=1, le=100, description="Количество записей"),
    repo: TradingRepository = Depends(get_repository),
    redis: aioredis.Redis = Depends(get_redis),
) -> dict[str, Any]:
    cache_key = f"results:{oil_id}:{delivery_type_id}:{delivery_basis_id}:{limit}"

    async def fetch() -> list[dict]:
        trades = await repo.get_trading_results(
            oil_id, delivery_type_id, delivery_basis_id, limit
        )
        return [TradingResult.model_validate(t).model_dump(mode="json") for t in trades]

    return await cached_response(redis, cache_key, fetch)