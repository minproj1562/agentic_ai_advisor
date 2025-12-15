# app/api/middleware/rate_limit.py
"""
Rate limiting middleware
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings
from app.core.cache import CacheManager
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.cache = CacheManager()
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self.window = settings.RATE_LIMIT_PERIOD
    
    async def dispatch(self, request: Request, call_next):
        """
        Check rate limits for each request
        """
        # Skip rate limiting for certain paths
        if self._is_exempt_path(request.url.path):
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if not await self._check_rate_limit(client_id):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": self.window
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Window"] = str(self.window)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get client identifier for rate limiting
        """
        # Try to get authenticated user ID
        if hasattr(request.state, "user"):
            return f"user:{request.state.user.get('uid')}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(self, client_id: str) -> bool:
        """
        Check if client has exceeded rate limit
        """
        key = f"rate_limit:{client_id}"
        
        try:
            # Increment counter
            current = self.cache.increment(key)
            
            if current == 1:
                # First request in window, set expiration
                self.cache.redis_client.expire(key, self.window)
            
            # Check if limit exceeded
            if current > self.max_requests:
                logger.warning(f"Rate limit exceeded for {client_id}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            # Allow request on error
            return True
    
    def _is_exempt_path(self, path: str) -> bool:
        """
        Check if path is exempt from rate limiting
        """
        exempt_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        
        return path in exempt_paths