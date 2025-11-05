# app/api/middleware/auth.py
"""
Authentication middleware for FastAPI
"""

from fastapi import Request, HTTPException
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings
from app.core.security import decode_token
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware to verify JWT tokens
    """
    
    # Paths that don't require authentication
    EXEMPT_PATHS = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh-token",
        "/metrics",
    ]
    
    async def dispatch(self, request: Request, call_next):
        """
        Process each request for authentication
        """
        # Check if path is exempt
        if self._is_exempt_path(request.url.path):
            return await call_next(request)
        
        # Get authorization header
        authorization = request.headers.get("Authorization")
        
        if not authorization:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header missing"}
            )
        
        # Extract token
        scheme, token = get_authorization_scheme_param(authorization)
        
        if scheme.lower() != "bearer":
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authentication scheme"}
            )
        
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token missing"}
            )
        
        try:
            # Decode and verify token
            payload = decode_token(token)
            
            # Add user info to request state
            request.state.user = payload
            request.state.token = token
            
            # Log request
            logger.info(
                f"Authenticated request: {request.method} {request.url.path} "
                f"by user: {payload.get('uid')}"
            )
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"}
            )
        
        # Process request
        response = await call_next(request)
        
        return response
    
    def _is_exempt_path(self, path: str) -> bool:
        """
        Check if path is exempt from authentication
        """
        # Exact match
        if path in self.EXEMPT_PATHS:
            return True
        
        # Prefix match for WebSocket paths
        if path.startswith("/api/v1/ws/"):
            return True
        
        # Static files
        if path.startswith("/static/"):
            return True
        
        return False