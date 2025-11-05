"""
Cache management with Redis
Enterprise-level caching implementation
"""

import json
import pickle
from datetime import timedelta
from functools import wraps
from typing import Any, Optional

import redis
from redis import ConnectionPool

from app.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class CacheManager:
    """
    Advanced cache manager with Redis
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Redis connection"""
        try:
            self.pool = ConnectionPool(
                host=settings.REDIS_URL.split("://")[1].split(":")[0],
                port=int(settings.REDIS_URL.split(":")[-1].split("/")[0]),
                db=int(settings.REDIS_URL.split("/")[-1]),
                password=settings.REDIS_PASSWORD,
                max_connections=settings.REDIS_POOL_SIZE,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 1,  # TCP_KEEPINTVL
                    3: 5,  # TCP_KEEPCNT
                }
            )
            
            self.redis_client = redis.Redis(
                connection_pool=self.pool,
                decode_responses=False
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {str(e)}")
            # Fallback to in-memory cache
            self.redis_client = None
            self.memory_cache = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            full_key = f"{settings.CACHE_PREFIX}:{key}"
            
            if self.redis_client:
                value = self.redis_client.get(full_key)
                if value:
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        try:
                            return pickle.loads(value)
                        except:
                            return value.decode() if isinstance(value, bytes) else value
            else:
                # Fallback to memory cache
                return self.memory_cache.get(full_key)
                
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        try:
            full_key = f"{settings.CACHE_PREFIX}:{key}"
            ttl = ttl or settings.CACHE_TTL
            
            # Serialize value
            try:
                serialized = json.dumps(value, default=str)
            except (TypeError, ValueError):
                serialized = pickle.dumps(value)
            
            if self.redis_client:
                return self.redis_client.setex(
                    full_key,
                    ttl,
                    serialized
                )
            else:
                # Fallback to memory cache
                self.memory_cache[full_key] = value
                return True
                
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            full_key = f"{settings.CACHE_PREFIX}:{key}"
            
            if self.redis_client:
                return bool(self.redis_client.delete(full_key))
            else:
                if full_key in self.memory_cache:
                    del self.memory_cache[full_key]
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            full_key = f"{settings.CACHE_PREFIX}:{key}"
            
            if self.redis_client:
                return bool(self.redis_client.exists(full_key))
            else:
                return full_key in self.memory_cache
                
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {str(e)}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        try:
            full_key = f"{settings.CACHE_PREFIX}:{key}"
            
            if self.redis_client:
                return self.redis_client.incr(full_key, amount)
            else:
                current = self.memory_cache.get(full_key, 0)
                self.memory_cache[full_key] = current + amount
                return self.memory_cache[full_key]
                
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {str(e)}")
            return 0
    
    def get_many(self, keys: list) -> dict:
        """Get multiple values"""
        try:
            full_keys = [f"{settings.CACHE_PREFIX}:{key}" for key in keys]
            result = {}
            
            if self.redis_client:
                values = self.redis_client.mget(full_keys)
                for key, value in zip(keys, values):
                    if value:
                        try:
                            result[key] = json.loads(value)
                        except:
                            result[key] = value
            else:
                for key in keys:
                    full_key = f"{settings.CACHE_PREFIX}:{key}"
                    if full_key in self.memory_cache:
                        result[key] = self.memory_cache[full_key]
            
            return result
            
        except Exception as e:
            logger.error(f"Cache get_many error: {str(e)}")
            return {}
    
    def set_many(self, mapping: dict, ttl: Optional[int] = None) -> bool:
        """Set multiple values"""
        try:
            ttl = ttl or settings.CACHE_TTL
            
            if self.redis_client:
                pipe = self.redis_client.pipeline()
                for key, value in mapping.items():
                    full_key = f"{settings.CACHE_PREFIX}:{key}"
                    try:
                        serialized = json.dumps(value, default=str)
                    except:
                        serialized = pickle.dumps(value)
                    pipe.setex(full_key, ttl, serialized)
                pipe.execute()
                return True
            else:
                for key, value in mapping.items():
                    full_key = f"{settings.CACHE_PREFIX}:{key}"
                    self.memory_cache[full_key] = value
                return True
                
        except Exception as e:
            logger.error(f"Cache set_many error: {str(e)}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        try:
            full_pattern = f"{settings.CACHE_PREFIX}:{pattern}"
            
            if self.redis_client:
                keys = self.redis_client.keys(full_pattern)
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            else:
                # Memory cache invalidation
                keys_to_delete = [
                    k for k in self.memory_cache.keys()
                    if k.startswith(full_pattern.replace("*", ""))
                ]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                return len(keys_to_delete)
                
        except Exception as e:
            logger.error(f"Cache invalidate pattern error: {str(e)}")
            return 0
    
    def clear_all(self) -> bool:
        """Clear all cache"""
        try:
            if self.redis_client:
                self.redis_client.flushdb()
            else:
                self.memory_cache.clear()
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return False


# Cache decorators
def cache_result(ttl: int = None, key_prefix: str = None):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = CacheManager()
            
            # Generate cache key
            cache_key = f"{key_prefix or func.__name__}:"
            cache_key += f"{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Check cache
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = CacheManager()
            
            # Generate cache key
            cache_key = f"{key_prefix or func.__name__}:"
            cache_key += f"{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Check cache
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            
            return result
        
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def invalidate_cache(pattern: str):
    """Decorator to invalidate cache after function execution"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            cache = CacheManager()
            cache.invalidate_pattern(pattern)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            cache = CacheManager()
            cache.invalidate_pattern(pattern)
            return result
        
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


async def check_redis_health() -> dict:
    """Check Redis health"""
    try:
        cache = CacheManager()
        
        if cache.redis_client:
            cache.redis_client.ping()
            info = cache.redis_client.info()
            
            return {
                "status": "healthy",
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human"),
                "uptime_days": info.get("uptime_in_days")
            }
        else:
            return {
                "status": "degraded",
                "message": "Using in-memory cache"
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }