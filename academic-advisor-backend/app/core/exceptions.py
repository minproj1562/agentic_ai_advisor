# app/core/exceptions.py
"""
Custom exceptions for the application
"""

from typing import Any, Dict, Optional


class BaseException(Exception):
    """
    Base exception class
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class CustomException(BaseException):
    """
    Custom exception for API errors
    """
    pass


class AuthenticationException(BaseException):
    """
    Authentication related exceptions
    """
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            details=details
        )


class AuthorizationException(BaseException):
    """
    Authorization related exceptions
    """
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            details=details
        )


class ValidationException(BaseException):
    """
    Data validation exceptions
    """
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details
        )


class NotFoundException(BaseException):
    """
    Resource not found exceptions
    """
    
    def __init__(self, resource: str = "Resource", details: Optional[Dict] = None):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            error_code="NOT_FOUND",
            details=details
        )


class ConflictException(BaseException):
    """
    Resource conflict exceptions
    """
    
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details
        )


class RateLimitException(BaseException):
    """
    Rate limit exceeded exceptions
    """
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details
        )


class FirebaseException(BaseException):
    """
    Firebase related exceptions
    """
    
    def __init__(self, message: str = "Firebase operation failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="FIREBASE_ERROR",
            details=details
        )


class MLModelException(BaseException):
    """
    ML model related exceptions
    """
    
    def __init__(self, message: str = "ML model error", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="ML_MODEL_ERROR",
            details=details
        )


class ServiceException(BaseException):
    """
    Service layer exceptions
    """
    
    def __init__(self, message: str = "Service error", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="SERVICE_ERROR",
            details=details
        )


class WebSocketException(BaseException):
    """
    WebSocket related exceptions
    """
    
    def __init__(self, message: str = "WebSocket error", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="WEBSOCKET_ERROR",
            details=details
        )

# Backward compatibility alias
DataNotFoundException = NotFoundException
