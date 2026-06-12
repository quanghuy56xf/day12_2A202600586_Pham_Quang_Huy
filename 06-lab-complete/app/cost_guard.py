"""Monthly budget guard — Redis-backed, per user."""
from datetime import datetime

import redis
from fastapi import HTTPException

from app.config import settings

PRICE_PER_1K_INPUT_TOKENS = 0.00015
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def _budget_key(user_id: str) -> str:
    month_key = datetime.now().strftime("%Y-%m")
    return f"budget:{user_id}:{month_key}"


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        (input_tokens / 1000) * PRICE_PER_1K_INPUT_TOKENS
        + (output_tokens / 1000) * PRICE_PER_1K_OUTPUT_TOKENS
    )


def check_budget(user_id: str, estimated_cost: float = 0.0) -> None:
    """Return if within budget; raise HTTP 402 if monthly limit exceeded."""
    r = get_redis()
    key = _budget_key(user_id)
    current = float(r.get(key) or 0)

    if current + estimated_cost > settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Monthly budget exceeded",
                "used_usd": round(current, 4),
                "budget_usd": settings.monthly_budget_usd,
                "resets_at": "first day of next month",
            },
        )


def record_usage(user_id: str, input_tokens: int, output_tokens: int) -> float:
    """Record token usage after LLM call."""
    cost = estimate_cost(input_tokens, output_tokens)
    r = get_redis()
    key = _budget_key(user_id)
    pipe = r.pipeline()
    pipe.incrbyfloat(key, cost)
    pipe.expire(key, 32 * 24 * 3600)
    pipe.execute()
    return cost
