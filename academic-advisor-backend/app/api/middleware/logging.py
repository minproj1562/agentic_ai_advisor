# app/api/middleware/logging.py
"""
Logging middleware for request/response tracking
"""

import json
import time
import uuid
from datetime import datetime

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive logging middleware
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Log each request and response
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timer
        start_time = time.time()
        
        # Log request
        await self._log_request(request, request_id)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            await self._log_response(request, response, duration, request_id)
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            
            return response
            
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            await self._log_error(request, e, duration, request_id)
            raise
    
    async def _log_request(self, request: Request, request_id: str):
        """
        Log incoming request
        """
        # Get request body if it's JSON
        body = None
        if request.headers.get("content-type") == "application/json":
            try:
                body = await request.body()
                # Reset body for the actual handler
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive
                body = json.loads(body) if body else None
            except:
                pass
        
        log_data = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "body": body if settings.DEBUG else None,  # Only log body in debug mode
        }
        
        # Add user info if authenticated
        if hasattr(request.state, "user"):
            log_data["user_id"] = request.state.user.get("uid")
        
        logger.info(f"Request: {json.dumps(log_data)}")
    
    async def _log_response(
        self,
        request: Request,
        response,
        duration: float,
        request_id: str
    ):
        """
        Log outgoing response
        """
        log_data = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": response.status_code,
            "duration": f"{duration:.3f}s",
            "path": request.url.path,
        }
        
        # Log warning for slow requests
        if duration > 1.0:
            logger.warning(f"Slow request: {json.dumps(log_data)}")
        else:
            logger.info(f"Response: {json.dumps(log_data)}")
    
    async def _log_error(
        self,
        request: Request,
        error: Exception,
        duration: float,
        request_id: str
    ):
        """
        Log error responses
        """
        log_data = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(error),
            "error_type": type(error).__name__,
            "duration": f"{duration:.3f}s",
            "path": request.url.path,
            "method": request.method,
        }
        
        logger.error(f"Error: {json.dumps(log_data)}")