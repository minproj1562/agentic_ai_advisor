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
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
        else:
            response = await call_next(request)
        
        # Add CORS headers to all responses
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Requested-With, X-Request-ID"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "*"
        
        return response

def setup_cors(app):
    """
    Configure CORS middleware with proper settings for dynamic frontend-backend communication
    """
    # Development origins
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    
    # Add custom CORS middleware first
    app.add_middleware(CORSMiddlewareFixed)
    
    # Add FastAPI CORS middleware
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