from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct
from datetime import date
from typing import Optional
from src.task3.models import SpimexTradingResults


async def get_last_trading_dates(
    db: AsyncSession,
    limit: int
) -> list[date]:
    result = await db.execute(
        select(distinct(SpimexTradingResults.date))
        .order_by(SpimexTradingResults.date.desc())
        .limit(limit)
    )
    return [row[0] for row in result.fetchall()]


async def get_dynamics(
    db: AsyncSession,
    start_date: date,
    end_date: date,
    oil_id: Optional[str] = None,
    delivery_type_id: Optional[str] = None,
    delivery_basis_id: Optional[str] = None,
) -> list[SpimexTradingResults]:
    query = (
        select(SpimexTradingResults)
        .where(SpimexTradingResults.date >= start_date)
        .where(SpimexTradingResults.date <= end_date)
        .order_by(SpimexTradingResults.date.desc())
    )

    if oil_id:
        query = query.where(SpimexTradingResults.oil_id == oil_id)
    if delivery_type_id:
        query = query.where(SpimexTradingResults.delivery_type_id == delivery_type_id)
    if delivery_basis_id:
        query = query.where(SpimexTradingResults.delivery_basis_id == delivery_basis_id)

    result = await db.execute(query)
    return result.scalars().all()


async def get_trading_results(
    db: AsyncSession,
    oil_id: Optional[str] = None,
    delivery_type_id: Optional[str] = None,
    delivery_basis_id: Optional[str] = None,
    limit: int = 10,
) -> list[SpimexTradingResults]:
    query = (
        select(SpimexTradingResults)
        .order_by(SpimexTradingResults.date.desc())
        .limit(limit)
    )

    if oil_id:
        query = query.where(SpimexTradingResults.oil_id == oil_id)
    if delivery_type_id:
        query = query.where(SpimexTradingResults.delivery_type_id == delivery_type_id)
    if delivery_basis_id:
        query = query.where(SpimexTradingResults.delivery_basis_id == delivery_basis_id)

    result = await db.execute(query)
    return result.scalars().all()