import redis
import json
from typing import Any, Optional
from app.core.config import settings
import structlog

logger = structlog.get_logger()

class CacheService:
    def __init__(self):
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("Cache get error", key=key, error=str(e))
            return None
    
    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        try:
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, expire, serialized_value)
        except Exception as e:
            logger.error("Cache set error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error("Cache delete error", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error("Cache exists error", key=key, error=str(e))
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        try:
            return self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error("Cache increment error", key=key, error=str(e))
            return None
    
    async def expire(self, key: str, seconds: int) -> bool:
        try:
            return bool(self.redis_client.expire(key, seconds))
        except Exception as e:
            logger.error("Cache expire error", key=key, error=str(e))
            return False

cache = CacheService()
