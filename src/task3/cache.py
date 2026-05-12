import json
from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from typing import Any, Optional
from redis.asyncio import Redis
from src.task3.config import settings


def seconds_until_cache_reset() -> int:
    now = datetime.now()
    reset_time = now.replace(hour=14, minute=11, second=0, microsecond=0)

    if now >= reset_time:
        reset_time += timedelta(days=1)

    return int((reset_time - now).total_seconds())


async def get_redis() -> AsyncIterator[Redis]:
    async with Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
    ) as client:
        yield client


class CacheContext:

    def __init__(self, redis: Redis, key: str) -> None:
        self.redis = redis
        self.key = key
        self.data: Optional[Any] = None

    async def __aenter__(self) -> "CacheContext":
        value = await self.redis.get(self.key)
        if value is not None:
            self.data = json.loads(value)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    async def set(self, data: Any) -> None:
        ttl = seconds_until_cache_reset()

        if ttl < 60:
            return

        await self.redis.setex(
            self.key,
            ttl,
            json.dumps(data, default=str),
        )