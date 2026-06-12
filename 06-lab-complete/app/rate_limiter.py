"""Redis-based sliding window rate limiter."""
import time

import redis
from fastapi import HTTPException

from app.config import settings

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def check_rate_limit(user_id: str) -> None:
    """
    Sliding window rate limit per user.
    Raises HTTP 429 when limit exceeded.
    """
    r = get_redis()
    now = time.time()
    window_start = now - 60
    key = f"ratelimit:{user_id}"

    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zcard(key)
    results = pipe.execute()

    current_count = results[1]
    if current_count >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": settings.rate_limit_per_minute,
                "window_seconds": 60,
            },
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(settings.rate_limit_per_minute),
                "X-RateLimit-Remaining": "0",
            },
        )

    r.zadd(key, {str(now): now})
    r.expire(key, 120)
