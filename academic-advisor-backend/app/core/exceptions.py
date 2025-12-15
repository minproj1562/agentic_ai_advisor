#academic-advisor-backend/app/core/exceptions.py
from fastapi import HTTPException, status
from typing import Any, Optional, Dict

class CustomException(HTTPException):
    """Base custom exception for the application"""
    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Any = None,
        code: str = None,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.code = code

class ValidationException(CustomException):
    """Exception for validation errors"""
    
    def __init__(self, detail: str, code: str = "VALIDATION_ERROR"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            code=code
        )

class AuthenticationException(CustomException):
    """Exception for authentication errors"""
    
    def __init__(self, detail: str = "Authentication failed", code: str = "AUTH_ERROR"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            code=code
        )

class AuthorizationException(CustomException):
    """Exception for authorization errors"""
    
    def __init__(self, detail: str = "Insufficient permissions", code: str = "AUTHZ_ERROR"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            code=code
        )

class NotFoundException(CustomException):
    """Exception for resource not found errors"""
    
    def __init__(self, detail: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            code=code
        )

class ConflictException(CustomException):
    """Exception for resource conflict errors"""
    
    def __init__(self, detail: str = "Resource already exists", code: str = "CONFLICT"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            code=code
        )

class RateLimitException(CustomException):
    """Exception for rate limiting"""
    
    def __init__(self, detail: str = "Rate limit exceeded", code: str = "RATE_LIMIT"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            code=code
        )

class ExternalServiceException(CustomException):
    """Exception for external service errors"""
    
    def __init__(self, detail: str = "External service error", code: str = "EXTERNAL_SERVICE_ERROR"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
            code=code
        )

class DatabaseException(CustomException):
    """Exception for database errors"""
    
    def __init__(self, detail: str = "Database error", code: str = "DATABASE_ERROR"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            code=code
        )

class FileProcessingException(CustomException):
    """Exception for file processing errors"""
    
    def __init__(self, detail: str = "File processing error", code: str = "FILE_PROCESSING_ERROR"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            code=code
        )

class CVProcessingException(CustomException):
    """Exception for CV processing errors"""
    
    def __init__(self, detail: str = "CV processing error", code: str = "CV_PROCESSING_ERROR"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            code=code
        )

class MLServiceException(CustomException):
    """Exception for ML service errors"""
    
    def __init__(self, detail: str = "ML service error", code: str = "ML_SERVICE_ERROR"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            code=code
        )

class FirebaseException(CustomException):
    """Exception for Firebase service errors"""
    
    def __init__(self, detail: str = "Firebase service error", code: str = "FIREBASE_ERROR"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            code=code
        )

class RedisException(CustomException):
    """Exception for Redis service errors"""
    
    def __init__(self, detail: str = "Redis service error", code: str = "REDIS_ERROR"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            code=code
        )

# Specific CV-related exceptions
class CVValidationException(ValidationException):
    """Exception for CV validation errors"""
    
    def __init__(self, detail: str, code: str = "CV_VALIDATION_ERROR"):
        super().__init__(detail=detail, code=code)

class CVParseException(FileProcessingException):
    """Exception for CV parsing errors"""
    
    def __init__(self, detail: str = "Failed to parse CV", code: str = "CV_PARSE_ERROR"):
        super().__init__(detail=detail, code=code)

class CVAnalysisException(CVProcessingException):
    """Exception for CV analysis errors"""
    
    def __init__(self, detail: str = "Failed to analyze CV", code: str = "CV_ANALYSIS_ERROR"):
        super().__init__(detail=detail, code=code)

# Research area exceptions
class ResearchAreaException(CustomException):
    """Exception for research area errors"""
    
    def __init__(self, detail: str = "Research area error", code: str = "RESEARCH_AREA_ERROR"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            code=code
        )

class ResearchAreaExtractionException(ResearchAreaException):
    """Exception for research area extraction errors"""
    
    def __init__(self, detail: str = "Failed to extract research areas", code: str = "RESEARCH_EXTRACTION_ERROR"):
        super().__init__(detail=detail, code=code)

# Export all exceptions
__all__ = [
    'CustomException',
    'ValidationException',
    'AuthenticationException',
    'AuthorizationException',
    'NotFoundException',
    'ConflictException',
    'RateLimitException',
    'ExternalServiceException',
    'DatabaseException',
    'FileProcessingException',
    'CVProcessingException',
    'MLServiceException',
    'FirebaseException',
    'RedisException',
    'CVValidationException',
    'CVParseException',
    'CVAnalysisException',
    'ResearchAreaException',
    'ResearchAreaExtractionException'
]