"""Redis-backed conversation history — stateless agent design."""
import json
from datetime import datetime, timezone

import redis

from app.config import settings

_redis: redis.Redis | None = None
MAX_HISTORY = 20


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def _history_key(user_id: str) -> str:
    return f"history:{user_id}"


def get_history(user_id: str) -> list[dict]:
    r = get_redis()
    data = r.get(_history_key(user_id))
    if not data:
        return []
    return json.loads(data)


def append_message(user_id: str, role: str, content: str) -> list[dict]:
    r = get_redis()
    key = _history_key(user_id)
    history = get_history(user_id)
    history.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
    r.setex(key, settings.session_ttl_seconds, json.dumps(history))
    return history


def ping_redis() -> bool:
    try:
        get_redis().ping()
        return True
    except Exception:
        return False
