"""
Performance optimization utilities
"""

import asyncio
from functools import lru_cache, wraps
from typing import Any, Callable
import aiocache
from aiocache import cached

from app.config import settings

# Configure aiocache
aiocache.caches.set_config({
    'default': {
        'cache': "aiocache.SimpleMemoryCache",
        'serializer': {
            'class': "aiocache.serializers.JsonSerializer"
        },
        'ttl': settings.CACHE_TTL,
    },
    'redis': {
        'cache': "aiocache.RedisCache",
        'endpoint': settings.REDIS_URL.split('://')[1].split(':')[0],
        'port': int(settings.REDIS_URL.split(':')[-1].split('/')[0]),
        'serializer': {
            'class': "aiocache.serializers.JsonSerializer"
        },
        'ttl': settings.CACHE_TTL,
    }
})

def async_cache(ttl: int = 300, cache_type: str = 'default'):
    """Async cache decorator"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @cached(ttl=ttl, cache=cache_type)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def batch_process(batch_size: int = 100):
    """Process data in batches"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(data: list, *args, **kwargs):
            results = []
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                batch_results = await func(batch, *args, **kwargs)
                results.extend(batch_results)
            return results
        return wrapper
    return decorator

class ConnectionPool:
    """Database connection pool manager"""
    
    def __init__(self, min_size: int = 10, max_size: int = 100):
        self.min_size = min_size
        self.max_size = max_size
        self._pool = []
        self._used = set()
        
    async def acquire(self):
        """Acquire connection from pool"""
        # Implementation
        pass
    
    async def release(self, conn):
        """Release connection back to pool"""
        # Implementation
        pass