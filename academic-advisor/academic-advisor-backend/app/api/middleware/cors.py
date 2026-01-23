# app/api/middleware/cors.py
"""
CORS Middleware Configuration
Handles Cross-Origin Resource Sharing for frontend-backend communication
"""

from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings


class CORSMiddlewareFixed(BaseHTTPMiddleware):
    """
    Custom CORS middleware to ensure proper headers for all requests
    """
    async def dispatch(self, request: Request, call_next):
        # Get origin from request
        origin = request.headers.get("origin", "")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            response.status_code = 200
        else:
            response = await call_next(request)
        
        # Add CORS headers - use settings instead of hardcoded values
        allowed_origins = settings.CORS_ORIGINS
        
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
        elif "*" in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        else:
            # Default to first allowed origin for non-matching requests
            response.headers["Access-Control-Allow-Origin"] = allowed_origins[0] if allowed_origins else "http://localhost:5173"
        
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Requested-With, X-Request-ID, Accept"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "Content-Length, X-Request-ID"
        response.headers["Access-Control-Max-Age"] = "600"
        
        return response


def setup_cors(app):
    """
    Configure CORS middleware with proper settings for dynamic frontend-backend communication
    """
    # Use settings for origins - includes both 3000 and 5173
    origins = settings.CORS_ORIGINS
    
    # Add custom CORS middleware first (handles preflight properly)
    app.add_middleware(CORSMiddlewareFixed)
    
    # Add FastAPI CORS middleware as backup
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600,
    )
    
    print(f"🔧 CORS Enabled for origins: {origins}")
    
    return app