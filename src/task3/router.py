from collections.abc import Callable, Awaitable
from datetime import date
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from src.task3.cache import CacheContext, get_redis
from src.task3.database import get_db
from src.task3.repository import TradingRepository


router = APIRouter(prefix="/trading", tags=["Trading"])


def get_repository(
    db: AsyncSession = Depends(get_db),
) -> TradingRepository:
    return TradingRepository(db)


async def fetch_cached_response(
    redis: Redis,
    cache_key: str,
    data: Any,
    response_key: str = "data",
) -> dict[str, Any]:
    async with CacheContext(redis, cache_key) as cache:
        if cache.data is not None:
            return {
                response_key: cache.data,
                "meta": {"count": len(cache.data)},
            }

        await cache.set(data)

    return {
        response_key: data,
        "meta": {"count": len(data)},
    }


@router.get("/last-dates")
async def get_last_trading_dates(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Количество последних торговых дней",
    ),
    repo: TradingRepository = Depends(get_repository),
    redis: Redis = Depends(get_redis),
) -> dict[str, Any]:
    cache_key = f"last_dates:{limit}"

    dates = await repo.get_last_trading_dates(limit)

    return await fetch_cached_response(redis, cache_key, dates, response_key="dates")


@router.get("/dynamics")
async def calculate_dynamics(
    start_date: date = Query(description="Начало периода (YYYY-MM-DD)"),
    end_date: date = Query(description="Конец периода (YYYY-MM-DD)"),
    oil_id: Optional[str] = Query(default=None, description="Код нефтепродукта (4 символа)"),
    delivery_type_id: Optional[str] = Query(default=None, description="Тип поставки (1 символ)"),
    delivery_basis_id: Optional[str] = Query(default=None, description="Базис поставки (3 символа)"),
    repo: TradingRepository = Depends(get_repository),
    redis: Redis = Depends(get_redis),
) -> dict[str, Any]:
    cache_key = (
        f"dynamics:{start_date}:{end_date}"
        f":{oil_id}:{delivery_type_id}:{delivery_basis_id}"
    )

    trades = await repo.get_dynamics(
        start_date,
        end_date,
        oil_id,
        delivery_type_id,
        delivery_basis_id,
    )

    return await fetch_cached_response(redis, cache_key, trades)


@router.get("/results")
async def fetch_trading_results(
    oil_id: Optional[str] = Query(default=None, description="Код нефтепродукта"),
    delivery_type_id: Optional[str] = Query(default=None, description="Тип поставки"),
    delivery_basis_id: Optional[str] = Query(default=None, description="Базис поставки"),
    limit: int = Query(default=10, ge=1, le=100, description="Количество записей"),
    repo: TradingRepository = Depends(get_repository),
    redis: Redis = Depends(get_redis),
) -> dict[str, Any]:
    cache_key = f"results:{oil_id}:{delivery_type_id}:{delivery_basis_id}:{limit}"

    trades = await repo.get_trading_results(
        oil_id,
        delivery_type_id,
        delivery_basis_id,
        limit,
    )

    return await fetch_cached_response(redis, cache_key, trades)