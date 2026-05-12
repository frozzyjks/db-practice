import pytest
import json
from unittest.mock import AsyncMock
from httpx import AsyncClient


async def test_root_endpoint(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "SPIMEX Trading API", "docs": "/docs"}


@pytest.mark.parametrize("limit, expected_status", [
    (5, 200),
    (101, 422),
    (0, 422),
])
async def test_last_dates_params(client: AsyncClient, limit: int, expected_status: int) -> None:
    response = await client.get(f"/trading/last-dates?limit={limit}")
    assert response.status_code == expected_status


async def test_last_dates_response_structure(client: AsyncClient) -> None:
    response = await client.get("/trading/last-dates")
    data = response.json()

    assert "dates" in data
    assert "meta" in data
    assert "count" in data["meta"]


async def test_dynamics_missing_start_date_returns_422(client: AsyncClient) -> None:
    response = await client.get(
        "/trading/dynamics?end_date=2025-01-31"
    )
    assert response.status_code == 422


async def test_dynamics_missing_end_date_returns_422(client: AsyncClient) -> None:
    response = await client.get(
        "/trading/dynamics?start_date=2025-01-01"
    )
    assert response.status_code == 422


async def test_dynamics_with_required_params(client: AsyncClient, mock_redis: AsyncMock) -> None:
    mock_redis.get.return_value = None

    response = await client.get(
        "/trading/dynamics"
        "?start_date=2025-01-01"
        "&end_date=2025-01-31"
    )
    assert response.status_code == 200

    data = response.json()
    assert "data" in data
    assert "meta" in data

    assert mock_redis.setex.called


@pytest.mark.parametrize("oil_id, delivery_type_id, delivery_basis_id", [
    ("A100", None, None),
    (None, "F", None),
    (None, None, "NVY"),
    (None, None, None),
])
async def test_dynamics_optional_filters(
    client: AsyncClient,
    oil_id: str | None,
    delivery_type_id: str | None,
    delivery_basis_id: str | None,
) -> None:
    params = {
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
    }
    if oil_id:
        params["oil_id"] = oil_id
    if delivery_type_id:
        params["delivery_type_id"] = delivery_type_id
    if delivery_basis_id:
        params["delivery_basis_id"] = delivery_basis_id

    response = await client.get("/trading/dynamics", params=params)
    assert response.status_code == 200


async def test_results_returns_200(client: AsyncClient) -> None:
    response = await client.get("/trading/results")
    assert response.status_code == 200


async def test_results_response_structure(client: AsyncClient) -> None:
    response = await client.get("/trading/results")
    data = response.json()

    assert "data" in data
    assert "meta" in data
    assert "count" in data["meta"]


@pytest.mark.parametrize("limit, expected_status", [
    (10, 200),
    (100, 200),
    (0, 422),
    (101, 422),
])
async def test_results_limit_validation(client: AsyncClient, limit: int, expected_status: int) -> None:
    response = await client.get(f"/trading/results?limit={limit}")
    assert response.status_code == expected_status


async def test_cache_hit_returns_cached_data(client: AsyncClient, mock_redis: AsyncMock) -> None:
    cached_dates = ["2025-01-10", "2025-01-09"]
    mock_redis.get.return_value = json.dumps(cached_dates)

    response = await client.get("/trading/last-dates?limit=2")

    assert response.status_code == 200
    data = response.json()
    assert data["dates"] == cached_dates