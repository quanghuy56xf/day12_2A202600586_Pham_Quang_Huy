"""Redis-backed conversation history — stateless agent design."""
import json
from datetime import datetime, timezone

from app.config import settings
from app.redis_client import get_redis, ping_redis

MAX_HISTORY = 20


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
