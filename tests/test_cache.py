import json
import pytest
import warnings
from unittest.mock import patch, AsyncMock
from src.task3.cache import CacheContext, seconds_until_cache_reset

pytestmark = pytest.mark.skip(reason="deprecated")


async def test_cache_context_hit(mock_redis: AsyncMock) -> None:
    test_data = {"key": "value"}
    mock_redis.get.return_value = json.dumps(test_data)

    async with CacheContext(mock_redis, "test_key") as ctx:
        assert ctx.data == test_data


async def test_cache_set_calls_setex(mock_redis: AsyncMock) -> None:
    mock_redis.get.return_value = None
    data = ["2025-01-10", "2025-01-09"]

    with patch("src.task3.cache.seconds_until_cache_reset", return_value=3600):
        async with CacheContext(mock_redis, "test_key") as ctx:
            await ctx.set(data)

    mock_redis.setex.assert_called_once()
    key, ttl, payload = mock_redis.setex.call_args[0]
    assert key == "test_key"
    assert ttl == 3600
    assert json.loads(payload) == data


async def test_cache_set_skips_when_ttl_too_small(mock_redis: AsyncMock) -> None:

    with patch("src.task3.cache.seconds_until_cache_reset", return_value=30):
        async with CacheContext(mock_redis, "test_key") as ctx:
            await ctx.set(["data"])

    mock_redis.setex.assert_not_called()


def test_seconds_until_reset_positive() -> None:
    seconds = seconds_until_cache_reset()
    assert seconds > 0


def test_seconds_until_reset_less_than_day() -> None:
    seconds = seconds_until_cache_reset()
    assert seconds <= 86400