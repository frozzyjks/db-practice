import redis.asyncio as redis
import json
from datetime import datetime, time
from src.task3.config import REDIS_HOST, REDIS_PORT


def get_redis():
    return redis.Redis(
        host=REDIS_HOST,
        port=int(REDIS_PORT),
        decode_responses=True
    )


def seconds_until_cache_reset() -> int:
    now = datetime.now()
    reset_time = now.replace(hour=14, minute=11, second=0, microsecond=0)

    if now >= reset_time:
        from datetime import timedelta
        reset_time += timedelta(days=1)

    delta = reset_time - now
    return int(delta.total_seconds())


async def get_cached(redis_client, key: str):
    value = await redis_client.get(key)
    if value:
        return json.loads(value)
    return None


async def set_cached(redis_client, key: str, data):
    ttl = seconds_until_cache_reset()
    if ttl < 60:
        return
    await redis_client.setex(key, ttl, json.dumps(data, default=str))