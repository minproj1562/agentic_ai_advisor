# app/services/chatbot/cache_service.py
"""
Response Caching Service
In-memory cache with optional Redis backend
"""

import hashlib
import json
import logging
import time
from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Redis client (lazy loaded)
_redis_client = None
_redis_available = False


def _get_redis():
    """Lazy load Redis client."""
    global _redis_client, _redis_available
    
    if _redis_client is not None:
        return _redis_client if _redis_available else None
    
    try:
        from app.config import settings
        
        # Check if Redis is explicitly disabled
        if not getattr(settings, 'REDIS_ENABLED', True):
            logger.info("ℹ️ Redis disabled in settings - using in-memory cache only")
            _redis_available = False
            return None
        
        import redis
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        # Test connection
        _redis_client.ping()
        _redis_available = True
        logger.info("✅ Redis cache connected")
        return _redis_client
        
    except Exception as e:
        logger.info(f"ℹ️ Redis not available ({e}) - using in-memory cache only")
        _redis_available = False
        return None


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    value: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    hits: int = 0
    ttl_seconds: int = 3600  # 1 hour default
    
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl_seconds
    
    def touch(self):
        self.hits += 1


class LRUCache:
    """Simple LRU cache for in-memory caching."""
    
    def __init__(self, max_size: int = 500):
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.max_size = max_size
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if key not in self.cache:
            self.stats["misses"] += 1
            return None
        
        entry = self.cache[key]
        
        # Check expiration
        if entry.is_expired():
            del self.cache[key]
            self.stats["misses"] += 1
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        entry.touch()
        self.stats["hits"] += 1
        
        return entry.value
    
    def set(self, key: str, value: Dict[str, Any], ttl_seconds: int = 3600):
        # Evict oldest if at capacity
        while len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.stats["evictions"] += 1
        
        self.cache[key] = CacheEntry(value=value, ttl_seconds=ttl_seconds)
    
    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0
        return {
            **self.stats,
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate_pct": round(hit_rate, 2),
        }


class CacheService:
    """
    Multi-tier caching service.
    L1: In-memory LRU cache (fast, limited size)
    L2: Redis (optional, larger, shared across instances)
    """
    
    # Cache key prefixes
    PREFIX_RESPONSE = "chat:resp:"
    PREFIX_STUDENT = "chat:student:"
    PREFIX_SESSION = "chat:session:"
    
    # TTL settings (in seconds)
    TTL_RESPONSE = 3600      # 1 hour for responses
    TTL_STUDENT = 300        # 5 minutes for student data
    TTL_CONCEPT = 86400      # 24 hours for static concepts
    
    def __init__(self, memory_cache_size: int = 500):
        self.memory_cache = LRUCache(max_size=memory_cache_size)
        self.redis = None
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection (non-blocking)."""
        self.redis = _get_redis()
    
    @staticmethod
    def _generate_key(prefix: str, query: str, context: Optional[Dict] = None) -> str:
        """Generate cache key from query and context."""
        # Normalize query
        normalized = query.lower().strip()
        
        # Add relevant context to key
        context_str = ""
        if context:
            # Only include stable context elements in key
            relevant = {
                k: v for k, v in context.items()
                if k in ["semester", "branch", "intent"]
            }
            if relevant:
                context_str = json.dumps(relevant, sort_keys=True)
        
        # Create hash
        key_content = f"{normalized}:{context_str}"
        key_hash = hashlib.md5(key_content.encode()).hexdigest()[:16]
        
        return f"{prefix}{key_hash}"
    
    async def get_response(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached response for a query."""
        key = self._generate_key(self.PREFIX_RESPONSE, query, context)
        
        # Try L1 (memory) first
        result = self.memory_cache.get(key)
        if result:
            logger.debug(f"Cache L1 hit: {key[:20]}...")
            return result
        
        # Try L2 (Redis) if available
        if self.redis:
            try:
                cached = self.redis.get(key)
                if cached:
                    result = json.loads(cached)
                    # Promote to L1
                    self.memory_cache.set(key, result, self.TTL_RESPONSE)
                    logger.debug(f"Cache L2 hit: {key[:20]}...")
                    return result
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        
        return None
    
    async def set_response(
        self,
        query: str,
        response: Dict[str, Any],
        context: Optional[Dict] = None,
        ttl: Optional[int] = None
    ):
        """Cache a response."""
        key = self._generate_key(self.PREFIX_RESPONSE, query, context)
        ttl = ttl or self.TTL_RESPONSE
        
        # Determine if response is cacheable
        if not self._is_cacheable(response):
            return
        
        # Store in L1
        self.memory_cache.set(key, response, ttl)
        
        # Store in L2 (Redis) if available
        if self.redis:
            try:
                self.redis.setex(key, ttl, json.dumps(response))
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
    
    def _is_cacheable(self, response: Dict[str, Any]) -> bool:
        """Check if response should be cached."""
        # Don't cache errors
        if response.get("type") == "error":
            return False
        
        # Don't cache low confidence responses
        if response.get("confidence") == "Low":
            return False
        
        # Don't cache performance analysis (too personalized)
        if response.get("type") == "performance_analysis":
            return False
        
        return True
    
    async def get_student_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached student data."""
        key = f"{self.PREFIX_STUDENT}{user_id}"
        
        # Try L1
        result = self.memory_cache.get(key)
        if result:
            return result
        
        # Try L2
        if self.redis:
            try:
                cached = self.redis.get(key)
                if cached:
                    result = json.loads(cached)
                    self.memory_cache.set(key, result, self.TTL_STUDENT)
                    return result
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        
        return None
    
    async def set_student_data(self, user_id: str, data: Dict[str, Any]):
        """Cache student data."""
        key = f"{self.PREFIX_STUDENT}{user_id}"
        
        self.memory_cache.set(key, data, self.TTL_STUDENT)
        
        if self.redis:
            try:
                self.redis.setex(key, self.TTL_STUDENT, json.dumps(data))
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
    
    async def invalidate_student_data(self, user_id: str):
        """Invalidate cached student data."""
        key = f"{self.PREFIX_STUDENT}{user_id}"
        self.memory_cache.delete(key)
        
        if self.redis:
            try:
                self.redis.delete(key)
            except Exception:
                pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "memory_cache": self.memory_cache.get_stats(),
            "redis_available": self.redis is not None,
        }
        
        if self.redis:
            try:
                info = self.redis.info("stats")
                stats["redis"] = {
                    "hits": info.get("keyspace_hits", 0),
                    "misses": info.get("keyspace_misses", 0),
                }
            except Exception:
                pass
        
        return stats
    
    def clear_all(self):
        """Clear all caches."""
        self.memory_cache.clear()
        if self.redis:
            try:
                # Only clear our prefixes
                for prefix in [self.PREFIX_RESPONSE, self.PREFIX_STUDENT, self.PREFIX_SESSION]:
                    keys = self.redis.keys(f"{prefix}*")
                    if keys:
                        self.redis.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis clear error: {e}")


# Singleton instance
_cache_service = None


def get_cache_service() -> CacheService:
    """Get or create cache service singleton."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service