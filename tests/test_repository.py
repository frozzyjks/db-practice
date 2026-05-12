import pytest
from datetime import date
from typing import Any
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.task3.models import SpimexTradingResults
from src.task3.repository import TradingRepository


async def create_record(session: AsyncSession, **kwargs: Any) -> None:
    defaults: dict[str, Any] = {
        "exchange_product_id": "A100NVY060F",
        "exchange_product_name": "Бензин АИ-100",
        "oil_id": "A100",
        "delivery_basis_id": "NVY",
        "delivery_type_id": "F",
        "delivery_basis_name": "Новороссийск",
        "volume": 100.0,
        "total": 10000.0,
        "count": 1,
        "date": date(2025, 1, 10),
    }
    defaults.update(kwargs)

    stmt = insert(SpimexTradingResults).values(**defaults)
    await session.execute(stmt)
    await session.flush()


async def test_get_last_dates_returns_list(db_session: AsyncSession) -> None:
    await create_record(db_session, date=date(2025, 1, 10))

    repo = TradingRepository(db_session)
    dates = await repo.get_last_trading_dates(limit=5)

    assert isinstance(dates, list)


async def test_get_last_dates_contains_inserted_date(db_session: AsyncSession) -> None:
    test_date = date(2025, 2, 15)
    await create_record(db_session, date=test_date)

    repo = TradingRepository(db_session)
    dates = await repo.get_last_trading_dates(limit=5)

    assert any(d == test_date for d in dates)


@pytest.mark.parametrize("limit", [1, 2, 3])
async def test_get_last_dates_respects_limit(db_session: AsyncSession, limit: int) -> None:
    for i in range(1, 4):
        await create_record(
            db_session,
            date=date(2025, 3, i),
            exchange_product_id=f"B{i}00NVY060F",
            oil_id=f"B{i}00",
        )

    repo = TradingRepository(db_session)
    dates = await repo.get_last_trading_dates(limit=limit)

    assert len(dates) <= limit


async def test_get_dynamics_filters_by_date_range(db_session: AsyncSession) -> None:
    await create_record(
        db_session,
        date=date(2025, 2, 10),
        exchange_product_id="C100NVY060F",
        oil_id="C100",
    )
    await create_record(
        db_session,
        date=date(2025, 1, 5),
        exchange_product_id="D100NVY060F",
        oil_id="D100",
    )

    repo = TradingRepository(db_session)
    trades = await repo.get_dynamics(
        start_date=date(2025, 2, 1),
        end_date=date(2025, 2, 28),
    )

    assert all(
        date(2025, 2, 1) <= trade.date <= date(2025, 2, 28)
        for trade in trades
    )


async def test_get_dynamics_filters_by_oil_id(db_session: AsyncSession) -> None:
    await create_record(
        db_session,
        date=date(2025, 4, 1),
        exchange_product_id="E100NVY060F",
        oil_id="E100",
    )
    await create_record(
        db_session,
        date=date(2025, 4, 2),
        exchange_product_id="F200NVY060F",
        oil_id="F200",
    )

    repo = TradingRepository(db_session)
    trades = await repo.get_dynamics(
        start_date=date(2025, 4, 1),
        end_date=date(2025, 4, 30),
        oil_id="E100",
    )

    assert len(trades) > 0
    assert all(trade.oil_id == "E100" for trade in trades)


async def test_get_dynamics_empty_for_no_data(db_session: AsyncSession) -> None:
    repo = TradingRepository(db_session)
    trades = await repo.get_dynamics(
        start_date=date(2020, 1, 1),
        end_date=date(2020, 12, 31),
    )

    assert trades == []


async def test_get_trading_results_returns_list(db_session: AsyncSession) -> None:
    await create_record(
        db_session,
        date=date(2025, 5, 1),
        exchange_product_id="G100NVY060F",
        oil_id="G100",
    )

    repo = TradingRepository(db_session)
    trades = await repo.get_trading_results()

    assert isinstance(trades, list)


@pytest.mark.parametrize("limit", [1, 2])
async def test_get_trading_results_respects_limit(db_session: AsyncSession, limit: int) -> None:
    for i in range(1, 4):
        await create_record(
            db_session,
            date=date(2025, 6, i),
            exchange_product_id=f"H{i}00NVY060F",
            oil_id=f"H{i}00",
        )

    repo = TradingRepository(db_session)
    trades = await repo.get_trading_results(limit=limit)

    assert len(trades) <= limit