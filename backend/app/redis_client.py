import logging
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)
_redis = None


async def get_redis():
    global _redis
    if _redis is None:
        try:
            _redis = redis.from_url(settings.redis_url, decode_responses=True)
            await _redis.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning(f"Redis unavailable: {e} — caching disabled")
            _redis = None
    return _redis


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
