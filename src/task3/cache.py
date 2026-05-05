import json
from datetime import datetime, timedelta
from typing import Any, Optional
import redis.asyncio as aioredis
from src.task3.config import settings


def seconds_until_cache_reset() -> int:
    now = datetime.now()
    reset_time = now.replace(hour=14, minute=11, second=0, microsecond=0)

    if now >= reset_time:
        reset_time += timedelta(days=1)

    return int((reset_time - now).total_seconds())


async def get_redis() -> aioredis.Redis:
    async with aioredis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
    ) as client:
        yield client


async def get_cached(
    redis: aioredis.Redis,
    key: str,
) -> Optional[Any]:
    value = await redis.get(key)
    if value:
        return json.loads(value)
    return None


async def set_cached(
    redis: aioredis.Redis,
    key: str,
    data: Any,
) -> None:
    ttl = seconds_until_cache_reset()

    if ttl < 60:
        return
    await redis.setex(key, ttl, json.dumps(data, default=str))