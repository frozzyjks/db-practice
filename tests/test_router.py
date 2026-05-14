import json
import pytest
from datetime import date
from unittest.mock import AsyncMock
from httpx import AsyncClient


async def test_last_dates_returns_correct_shape(client: AsyncClient, mock_repo: AsyncMock) -> None:
    mock_repo.get_last_trading_dates.return_value = ["2025-01-10", "2025-01-09"]

    response = await client.get("/trading/last-dates?limit=2")

    assert response.status_code == 200
    data = response.json()
    assert "dates" in data
    assert "meta" in data
    assert data["meta"]["count"] == len(data["dates"])


async def test_last_dates_from_cache_skips_repository(
    client: AsyncClient,
    mock_repo: AsyncMock,
    mock_redis: AsyncMock,
) -> None:
    cached = ["2025-01-10", "2025-01-09"]
    mock_redis.get.return_value = json.dumps(cached)

    response = await client.get("/trading/last-dates?limit=2")

    assert response.status_code == 200
    assert response.json()["dates"] == cached
    mock_repo.get_last_trading_dates.assert_not_called()


async def test_last_dates_cache_miss_calls_repo_and_saves_to_cache(
    client: AsyncClient,
    mock_repo: AsyncMock,
    mock_redis: AsyncMock,
) -> None:
    mock_redis.get.return_value = None
    mock_repo.get_last_trading_dates.return_value = ["2025-01-10"]

    response = await client.get("/trading/last-dates?limit=1")

    assert response.status_code == 200
    mock_repo.get_last_trading_dates.assert_called_once_with(1)
    mock_redis.setex.assert_called_once()


async def test_dynamics_returns_correct_shape(client: AsyncClient, mock_repo: AsyncMock) -> None:
    mock_repo.get_dynamics.return_value = [
        {"oil_id": "A100", "date": "2025-01-10"},
        {"oil_id": "A100", "date": "2025-01-11"},
    ]

    response = await client.get(
        "/trading/dynamics?start_date=2025-01-01&end_date=2025-01-31"
    )

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["meta"]["count"] == len(data["data"])


async def test_dynamics_passes_filters_to_repository(client: AsyncClient, mock_repo: AsyncMock) -> None:
    mock_repo.get_dynamics.return_value = []

    await client.get(
        "/trading/dynamics"
        "?start_date=2025-01-01"
        "&end_date=2025-01-31"
        "&oil_id=A100"
        "&delivery_type_id=F"
        "&delivery_basis_id=NVY"
    )

    mock_repo.get_dynamics.assert_called_once_with(
        date(2025, 1, 1),
        date(2025, 1, 31),
        "A100",
        "F",
        "NVY",
    )


async def test_dynamics_cache_hit_skips_repository(
    client: AsyncClient,
    mock_repo: AsyncMock,
    mock_redis: AsyncMock,
) -> None:
    cached_trades = [{"oil_id": "A100", "date": "2025-01-10"}]
    mock_redis.get.return_value = json.dumps(cached_trades)

    response = await client.get(
        "/trading/dynamics?start_date=2025-01-01&end_date=2025-01-31"
    )

    assert response.status_code == 200
    assert response.json()["data"] == cached_trades
    mock_repo.get_dynamics.assert_not_called()


async def test_results_returns_correct_shape(client: AsyncClient, mock_repo: AsyncMock) -> None:
    mock_repo.get_trading_results.return_value = [
        {"oil_id": "A100", "total": 50000},
        {"oil_id": "B200", "total": 30000},
    ]

    response = await client.get("/trading/results")

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert data["meta"]["count"] == len(data["data"])


async def test_results_cache_hit_skips_repository(
    client: AsyncClient,
    mock_repo: AsyncMock,
    mock_redis: AsyncMock,
) -> None:
    cached = [{"oil_id": "A100", "total": 99999}]
    mock_redis.get.return_value = json.dumps(cached)

    response = await client.get("/trading/results")

    assert response.status_code == 200
    assert response.json()["data"] == cached
    mock_repo.get_trading_results.assert_not_called()


async def test_results_cache_miss_saves_to_redis(
    client: AsyncClient,
    mock_repo: AsyncMock,
    mock_redis: AsyncMock,
) -> None:
    mock_redis.get.return_value = None
    mock_repo.get_trading_results.return_value = [{"oil_id": "A100"}]

    await client.get("/trading/results?limit=1")

    mock_redis.setex.assert_called_once()


async def test_results_passes_filters_to_repository(client: AsyncClient, mock_repo: AsyncMock) -> None:
    mock_repo.get_trading_results.return_value = []

    await client.get(
        "/trading/results?oil_id=A100&delivery_type_id=F&delivery_basis_id=NVY&limit=5"
    )

    mock_repo.get_trading_results.assert_called_once_with("A100", "F", "NVY", 5)