"""
Utility helpers for interacting with Redis as a distributed cache backend.
Ported from BERDataLakehouse/datalake-mcp-server for BERDLTable_conversion_service.
"""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional, cast, Union

try:
    import redis
    from redis.exceptions import RedisError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    class RedisError(Exception): pass

logger = logging.getLogger(__name__)

CachePayload = List[Dict[str, Any]]
REDIS_NAMESPACE_PREFIX = "berdl-service" # Changed from berdl-mcp

def _build_cache_key(namespace: str, cache_key: str) -> str:
    return f"{REDIS_NAMESPACE_PREFIX}:{namespace}:{cache_key}"

@lru_cache(maxsize=1)
def _get_redis_client() -> Optional['redis.Redis']:
    """
    Lazily create a Redis client backed by a connection pool.
    Uses environment variables REDIS_HOST and REDIS_PORT.
    PROD: these should be set in kbase config or docker env.
    LOCAL: defaults to localhost:6379.
    """
    if not REDIS_AVAILABLE:
        logger.warning("Redis package not installed. Caching disabled.")
        return None

    try:
        host = os.environ.get('REDIS_HOST', 'localhost')
        port = int(os.environ.get('REDIS_PORT', 6379))
        
        logger.info(
            "Initializing Redis client host=%s port=%s",
            host,
            port,
        )
        pool = redis.ConnectionPool(
            host=host, port=port
        )
        return redis.Redis(connection_pool=pool)
    except Exception as e:
        logger.exception(f"Failed to establish Redis connection pool; caching disabled. Error: {e}")
        return None


def get_cached_value(namespace: str, cache_key: str) -> Optional[Any]:
    """
    Retrieve a cached payload from Redis.
    """
    client = _get_redis_client()
    if client is None:
        return None

    redis_key = _build_cache_key(namespace, cache_key)

    try:
        # logger.info("Reading cache namespace=%s key=%s", namespace, cache_key)
        raw_value = client.get(redis_key)
        if raw_value is None:
            # logger.info("Cache miss for namespace=%s key=%s", namespace, cache_key)
            return None
            
        if isinstance(raw_value, bytes):
            decoded_value = raw_value.decode("utf-8")
        else:
            decoded_value = cast(str, raw_value)
            
        logger.info("Cache hit for namespace=%s key=%s", namespace, cache_key)
        return json.loads(decoded_value)
    except (Exception, json.JSONDecodeError) as e:
        logger.exception(
            "Redis connection error while fetching namespace=%s key=%s: %s",
            namespace,
            cache_key,
            str(e)
        )
        return None


def set_cached_value(
    namespace: str,
    cache_key: str,
    data: Any,
    ttl: int = 3600,
) -> None:
    """
    Store a payload in Redis with the provided TTL.
    """
    client = _get_redis_client()
    if client is None:
        return

    redis_key = _build_cache_key(namespace, cache_key)

    try:
        payload = json.dumps(data)
        client.set(name=redis_key, value=payload, ex=ttl)
        logger.info(
            "Cached value namespace=%s key=%s ttl=%ss", namespace, cache_key, ttl
        )
    except Exception as e:
        logger.exception(
            "Failed to cache value namespace=%s key=%s: %s", namespace, cache_key, str(e)
        )
