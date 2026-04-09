# app/utils/password.py
"""
Password generation and validation utilities
EMERGENCY FIX: Uses hashlib + salt instead of bcrypt when bcrypt fails
"""
import re
import secrets
import string
import hashlib
import base64
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# ✅ Try to use bcrypt, but have a complete fallback ready
try:
    from passlib.context import CryptContext
    
    # Simple bcrypt config to avoid complex initialization
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Test if bcrypt actually works
    test_hash = pwd_context.hash("test123")
    pwd_context.verify("test123", test_hash)
    
    BCRYPT_AVAILABLE = True
    logger.info("✅ Bcrypt available and working")
    
except Exception as e:
    logger.warning(f"⚠️ Bcrypt not available ({e}), using fallback hashing")
    BCRYPT_AVAILABLE = False
    pwd_context = None


# ✅ SAFE FALLBACK: SHA-256 + salt (when bcrypt fails)
def _generate_salt() -> str:
    """Generate a random salt for hashing"""
    return base64.b64encode(secrets.token_bytes(32)).decode('utf-8')


def _hash_with_salt(password: str, salt: str) -> str:
    """Hash password with SHA-256 + salt"""
    # Combine password and salt
    salted_password = f"{password}{salt}"
    
    # Hash with SHA-256 (multiple rounds for security)
    hash_obj = hashlib.sha256(salted_password.encode('utf-8'))
    for _ in range(10000):  # 10,000 rounds for security
        hash_obj = hashlib.sha256(hash_obj.digest())
    
    # Return salt:hash format
    return f"sha256${salt}${base64.b64encode(hash_obj.digest()).decode('utf-8')}"


def _verify_with_salt(password: str, stored_hash: str) -> bool:
    """Verify password against SHA-256 + salt hash"""
    try:
        if not stored_hash.startswith("sha256$"):
            return False
        
        parts = stored_hash.split('$')
        if len(parts) != 3:
            return False
        
        _, salt, expected_hash = parts
        
        # Hash the provided password with the same salt
        candidate_hash = _hash_with_salt(password, salt)
        
        # Compare hashes
        return candidate_hash == stored_hash
        
    except Exception as e:
        logger.error(f"Hash verification error: {e}")
        return False


def extract_admission_year_from_roll(roll_number: str) -> int:
    """
    Extract admission year from roll number.
    Format: 5023152 → 50 (dept) + 23 (year) + 152 (roll)
    Returns: 2023
    """
    if len(roll_number) < 4:
        raise ValueError("Invalid roll number format")
    
    # Extract year digits (positions 2-4, e.g., "23" from "5023152")
    year_digits = roll_number[2:4]
    
    # Convert to full year (23 → 2023, 24 → 2024)
    year_int = int(year_digits)
    
    # Handle century (assume 20xx for years 00-50, 19xx for 51-99)
    if year_int <= 50:
        full_year = 2000 + year_int
    else:
        full_year = 1900 + year_int
    
    return full_year


def generate_student_password(roll_number: str, admission_year: int = None) -> str:
    """
    Generate initial password for student.
    Format: {roll_number}@{admission_year}
    
    Example: 5023152@2023
    """
    if not admission_year:
        admission_year = extract_admission_year_from_roll(roll_number)
    
    return f"{roll_number}@{admission_year}"


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt or fallback method
    ✅ FIXED: Complete fallback when bcrypt fails
    """
    global BCRYPT_AVAILABLE
    
    # ✅ First, try bcrypt if available
    if BCRYPT_AVAILABLE and pwd_context:
        try:
            # Ensure password is within bcrypt limits
            if len(password.encode('utf-8')) > 72:
                password = password[:60]  # Conservative truncation
            
            return pwd_context.hash(password)
            
        except Exception as e:
            logger.warning(f"Bcrypt failed ({e}), switching to fallback permanently")
            BCRYPT_AVAILABLE = False
    
    # ✅ Fallback: Use SHA-256 + salt
    logger.info("Using SHA-256 + salt for password hashing")
    salt = _generate_salt()
    return _hash_with_salt(password, salt)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    ✅ FIXED: Handles both bcrypt and fallback hashes
    """
    global BCRYPT_AVAILABLE
    
    try:
        # ✅ Check if it's a SHA-256 hash (our fallback)
        if hashed_password.startswith("sha256$"):
            return _verify_with_salt(plain_password, hashed_password)
        
        # ✅ Try bcrypt if available and hash looks like bcrypt
        if BCRYPT_AVAILABLE and pwd_context and hashed_password.startswith("$2"):
            try:
                # Ensure password is within bcrypt limits
                if len(plain_password.encode('utf-8')) > 72:
                    plain_password = plain_password[:60]
                
                return pwd_context.verify(plain_password, hashed_password)
                
            except Exception as e:
                logger.warning(f"Bcrypt verification failed ({e}), disabling bcrypt")
                BCRYPT_AVAILABLE = False
        
        # ✅ If we reach here, the hash format is unknown
        logger.error(f"Unknown hash format: {hashed_password[:20]}...")
        return False
        
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def validate_roll_number(roll_number: str) -> Tuple[bool, str]:
    """
    Validate roll number format.
    Expected: 7 digits (e.g., 5023152)
    """
    if not roll_number:
        return False, "Roll number is required"
    
    if not roll_number.isdigit():
        return False, "Roll number must contain only digits"
    
    if len(roll_number) != 7:
        return False, "Roll number must be exactly 7 digits"
    
    return True, ""


def generate_random_password(length: int = 12) -> str:
    """
    Generate a random secure password.
    Used for faculty/admin accounts.
    """
    # Keep it reasonable length
    max_length = min(length, 50)
    
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(max_length))


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.
    Requirements: Min 8 chars, 1 uppercase, 1 lowercase, 1 digit
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 100:  # Reasonable upper limit
        return False, "Password is too long (maximum 100 characters)"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    return True, ""


# ✅ DIAGNOSTIC FUNCTION
def test_password_system():
    """Test the password system to ensure it's working"""
    try:
        test_password = "TestPass123"
        
        # Test hashing
        hashed = hash_password(test_password)
        logger.info(f"Hash created: {hashed[:50]}...")
        
        # Test verification
        is_valid = verify_password(test_password, hashed)
        logger.info(f"Verification result: {is_valid}")
        
        # Test with wrong password
        is_invalid = verify_password("WrongPass123", hashed)
        logger.info(f"Wrong password result: {is_invalid}")
        
        return is_valid and not is_invalid
        
    except Exception as e:
        logger.error(f"Password system test failed: {e}")
        return False


# ✅ Call test on import (optional)
if __name__ == "__main__":
    result = test_password_system()
    print(f"Password system working: {result}")