"""Redis-based sliding window rate limiter."""
import time

from fastapi import HTTPException

from app.config import settings
from app.redis_client import get_redis


def check_rate_limit(user_id: str) -> None:
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
