#academic-advisor-backend/app/core/security.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Import from the new firebase module
from app.core.firebase import verify_firebase_token as verify_firebase_token_util

# Security scheme
security = HTTPBearer()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class FirebaseUser:
    """Enhanced user model with role-based access"""
    def __init__(self, uid: str, email: str, role: str = "student"):
        self.uid = uid
        self.email = email
        self.role = role
    
    @property
    def is_faculty(self) -> bool:
        return self.role == "faculty"
    
    @property
    def is_student(self) -> bool:
        return self.role == "student"

async def verify_firebase_token(token: str) -> Dict[str, Any]:
    """Verify Firebase ID token with detailed error handling"""
    try:
        decoded_token = verify_firebase_token_util(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> FirebaseUser:
    """Get current authenticated user with role validation"""
    token = credentials.credentials
    
    try:
        decoded = await verify_firebase_token(token)
        role = decoded.get('role', 'student')
        
        return FirebaseUser(
            uid=decoded['uid'],
            email=decoded.get('email', ''),
            role=role
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def get_current_faculty(
    current_user: FirebaseUser = Depends(get_current_user)
) -> FirebaseUser:
    """Dependency for faculty-only routes (e.g., student analysis table)"""
    if not current_user.is_faculty:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faculty access required"
        )
    return current_user

async def get_current_student(
    current_user: FirebaseUser = Depends(get_current_user)
) -> FirebaseUser:
    """Dependency for student-only routes (e.g., project uploads)"""
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )
    return current_user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token for internal use"""
    from app.core.config import settings
    
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Create secure password hash"""
    return pwd_context.hash(password)