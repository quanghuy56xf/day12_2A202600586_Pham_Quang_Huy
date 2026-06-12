"""Shared Redis client — hỗ trợ Render Key Value (TLS + internal URL)."""
from __future__ import annotations

import logging
import ssl
from urllib.parse import urlparse

import redis

from app.config import settings

logger = logging.getLogger(__name__)
_redis: redis.Redis | None = None


def _redis_kwargs(url: str) -> dict:
    kwargs: dict = {
        "decode_responses": True,
        "socket_connect_timeout": 5,
        "socket_timeout": 5,
    }
    if url.startswith("rediss://"):
        kwargs["ssl_cert_reqs"] = ssl.CERT_NONE
        kwargs["ssl_check_hostname"] = False
    return kwargs


def create_redis(url: str) -> redis.Redis:
    return redis.from_url(url, **_redis_kwargs(url))


def reset_redis() -> None:
    global _redis
    if _redis is not None:
        try:
            _redis.close()
        except Exception:
            pass
    _redis = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        url = settings.redis_url
        if not url:
            raise ValueError("REDIS_URL is not configured")
        _redis = create_redis(url)
    return _redis


def _mask_url(url: str) -> str:
    if not url:
        return "(empty)"
    parsed = urlparse(url)
    host = parsed.hostname or "?"
    port = parsed.port or 6379
    return f"redis://***@{host}:{port}"


def ping_redis() -> bool:
    url = settings.redis_url
    if not url:
        logger.error("REDIS_URL is empty — check Render env / fromService link")
        return False

    candidates = [url]
    if url.startswith("redis://"):
        candidates.append(url.replace("redis://", "rediss://", 1))

    last_error: Exception | None = None
    for candidate in candidates:
        try:
            reset_redis()
            client = create_redis(candidate)
            client.ping()
            global _redis
            _redis = client
            if candidate != url:
                logger.info("Redis connected via TLS URL")
            return True
        except Exception as exc:
            last_error = exc
            logger.warning("Redis ping failed (%s): %s", _mask_url(candidate), exc)

    logger.error("Redis unavailable at %s — last error: %s", _mask_url(url), last_error)
    return False
