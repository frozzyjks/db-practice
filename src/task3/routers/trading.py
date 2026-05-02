from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import Optional

from src.task3.database import get_db
from src.task3.cache import get_redis, get_cached, set_cached
from src.task3 import repository
from src.task3.schemas import TradingResult

router = APIRouter(prefix="/trading", tags=["Trading"])


@router.get("/last-dates")
async def last_trading_dates(
    limit: int = Query(default=10, ge=1, le=100, description="Количество последних торговых дней"),
    db: AsyncSession = Depends(get_db),
):
    redis = get_redis()
    cache_key = f"last_dates:{limit}"

    cached = await get_cached(redis, cache_key)
    if cached:
        return {"dates": cached, "source": "cache"}

    dates = await repository.get_last_trading_dates(db, limit)
    result = [str(d) for d in dates]

    await set_cached(redis, cache_key, result)
    await redis.aclose()

    return {"dates": result, "source": "db"}


@router.get("/dynamics")
async def dynamics(
    start_date: date = Query(description="Начало периода (YYYY-MM-DD)"),
    end_date: date = Query(description="Конец периода (YYYY-MM-DD)"),
    oil_id: Optional[str] = Query(default=None, description="Код нефтепродукта (4 символа)"),
    delivery_type_id: Optional[str] = Query(default=None, description="Тип поставки (1 символ)"),
    delivery_basis_id: Optional[str] = Query(default=None, description="Базис поставки (3 символа)"),
    db: AsyncSession = Depends(get_db),
):
    redis = get_redis()
    cache_key = f"dynamics:{start_date}:{end_date}:{oil_id}:{delivery_type_id}:{delivery_basis_id}"

    cached = await get_cached(redis, cache_key)
    if cached:
        return {"data": cached, "source": "cache"}

    trades = await repository.get_dynamics(
        db, start_date, end_date, oil_id, delivery_type_id, delivery_basis_id
    )

    result = [TradingResult.model_validate(t).model_dump(mode="json") for t in trades]
    await set_cached(redis, cache_key, result)
    await redis.aclose()

    return {"data": result, "source": "db"}


@router.get("/results")
async def trading_results(
    oil_id: Optional[str] = Query(default=None),
    delivery_type_id: Optional[str] = Query(default=None),
    delivery_basis_id: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    redis = get_redis()
    cache_key = f"results:{oil_id}:{delivery_type_id}:{delivery_basis_id}:{limit}"

    cached = await get_cached(redis, cache_key)
    if cached:
        return {"data": cached, "source": "cache"}

    trades = await repository.get_trading_results(
        db, oil_id, delivery_type_id, delivery_basis_id, limit
    )

    result = [TradingResult.model_validate(t).model_dump(mode="json") for t in trades]
    await set_cached(redis, cache_key, result)
    await redis.aclose()

    return {"data": result, "source": "db"}