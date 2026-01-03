#academic-advisor-backend/app/utils/validators.py
import re
import os
from fastapi import UploadFile, HTTPException
from typing import Dict, Any, List, Tuple
import magic
from PIL import Image
import io
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FileValidationError(Exception):
    """Custom exception for file validation errors"""
    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

async def validate_file(
    file: UploadFile,
    max_size: int = 10 * 1024 * 1024,  # 10MB default
    allowed_types: List[str] = None,
    allowed_extensions: List[str] = None
) -> Dict[str, Any]:
    """
    Comprehensive file validation for CV uploads
    """
    if allowed_types is None:
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'image/jpeg',
            'image/png'
        ]
    
    if allowed_extensions is None:
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png']
    
    try:
        # Check if file is provided
        if not file or not file.filename:
            raise FileValidationError("No file provided", "NO_FILE")
        
        # Validate file size
        await _validate_file_size(file, max_size)
        
        # Validate file type and extension
        await _validate_file_type(file, allowed_types, allowed_extensions)
        
        # Validate file content (for security)
        await _validate_file_content(file)
        
        # Additional PDF-specific validation
        if file.content_type == 'application/pdf':
            await _validate_pdf_file(file)
        
        # Additional image validation
        if file.content_type and file.content_type.startswith('image/'):
            await _validate_image_file(file)
        
        return {
            "valid": True,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": await _get_file_size(file),
            "extension": os.path.splitext(file.filename)[1].lower()
        }
        
    except FileValidationError as e:
        return {
            "valid": False,
            "error": e.message,
            "code": e.code
        }
    except Exception as e:
        logger.error(f"Unexpected validation error: {str(e)}")
        return {
            "valid": False,
            "error": "File validation failed",
            "code": "VALIDATION_FAILED"
        }

async def _validate_file_size(file: UploadFile, max_size: int):
    """Validate file size"""
    # Get file size by reading content
    content = await file.read()
    file_size = len(content)
    
    # Reset file pointer
    await file.seek(0)
    
    if file_size > max_size:
        raise FileValidationError(
            f"File size {file_size // (1024 * 1024)}MB exceeds maximum allowed {max_size // (1024 * 1024)}MB",
            "FILE_TOO_LARGE"
        )
    
    if file_size == 0:
        raise FileValidationError("File is empty", "EMPTY_FILE")

async def _validate_file_type(file: UploadFile, allowed_types: List[str], allowed_extensions: List[str]):
    """Validate file type and extension"""
    filename = file.filename.lower()
    file_extension = os.path.splitext(filename)[1]
    
    # Check extension
    if file_extension not in allowed_extensions:
        raise FileValidationError(
            f"File extension {file_extension} not allowed. Allowed: {', '.join(allowed_extensions)}",
            "INVALID_EXTENSION"
        )
    
    # Check MIME type
    if file.content_type and file.content_type not in allowed_types:
        raise FileValidationError(
            f"File type {file.content_type} not allowed. Allowed: {', '.join(allowed_types)}",
            "INVALID_TYPE"
        )
    
    # Additional MIME type verification using python-magic
    try:
        content = await file.read(1024)  # Read first 1KB for magic number detection
        await file.seek(0)
        
        mime_type = magic.from_buffer(content, mime=True)
        
        # Map extensions to expected MIME types
        expected_mime_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png'
        }
        
        expected_mime = expected_mime_types.get(file_extension)
        if expected_mime and mime_type != expected_mime:
            raise FileValidationError(
                f"File content does not match extension. Expected {expected_mime}, got {mime_type}",
                "MIME_MISMATCH"
            )
            
    except ImportError:
        # python-magic not available, skip deep MIME validation
        logger.warning("python-magic not installed, skipping MIME validation")
    except Exception as e:
        logger.warning(f"MIME validation failed: {str(e)}")

async def _validate_file_content(file: UploadFile):
    """Validate file content for security"""
    # Read file content for basic security checks
    content = await file.read()
    await file.seek(0)
    
    # Check for null bytes (common in malicious files)
    if b'\x00' in content[:1024]:
        raise FileValidationError("File contains null bytes, potentially malicious", "MALICIOUS_CONTENT")
    
    # Check for executable markers
    executable_markers = [b'MZ', b'\x7fELF', b'#!']  # Windows PE, ELF, shebang
    for marker in executable_markers:
        if content.startswith(marker):
            raise FileValidationError("File appears to be executable, not allowed", "EXECUTABLE_FILE")

async def _validate_pdf_file(file: UploadFile):
    """Additional PDF file validation"""
    try:
        content = await file.read()
        await file.seek(0)
        
        # Basic PDF signature check
        if not content.startswith(b'%PDF'):
            raise FileValidationError("Invalid PDF file: missing PDF signature", "INVALID_PDF")
        
        # Check for PDF end marker
        if b'%%EOF' not in content[-1024:]:
            raise FileValidationError("Invalid PDF file: missing end-of-file marker", "INVALID_PDF_EOF")
        
        # Check file is not encrypted
        if b'/Encrypt' in content:
            raise FileValidationError("Encrypted PDF files are not supported", "ENCRYPTED_PDF")
            
    except Exception as e:
        if isinstance(e, FileValidationError):
            raise
        raise FileValidationError(f"PDF validation failed: {str(e)}", "PDF_VALIDATION_FAILED")

async def _validate_image_file(file: UploadFile):
    """Additional image file validation"""
    try:
        content = await file.read()
        await file.seek(0)
        
        # Validate image using PIL
        try:
            image = Image.open(io.BytesIO(content))
            image.verify()  # Verify it's a valid image
            
            # Reset for actual use
            image = Image.open(io.BytesIO(content))
            
            # Check dimensions (prevent extremely large images)
            max_dimension = 10000
            if max(image.size) > max_dimension:
                raise FileValidationError(
                    f"Image dimensions too large: {image.size}. Maximum allowed: {max_dimension}x{max_dimension}",
                    "IMAGE_TOO_LARGE"
                )
                
        except Exception as e:
            raise FileValidationError(f"Invalid image file: {str(e)}", "INVALID_IMAGE")
            
    except Exception as e:
        if isinstance(e, FileValidationError):
            raise
        raise FileValidationError(f"Image validation failed: {str(e)}", "IMAGE_VALIDATION_FAILED")

async def _get_file_size(file: UploadFile) -> int:
    """Get file size in bytes"""
    current_pos = await file.tell()
    await file.seek(0, 2)  # Seek to end
    size = await file.tell()
    await file.seek(current_pos)  # Reset position
    return size

def validate_doi(doi: str) -> bool:
    """Validate DOI format"""
    if not doi:
        return False
    
    # Remove any URL prefix
    doi = doi.strip()
    if doi.startswith('http'):
        # Extract DOI from URL
        match = re.search(r'10\.\d+/[^\s]+', doi)
        if match:
            doi = match.group(0)
    
    # Basic DOI pattern: 10.xxxx/yyyy
    doi_pattern = r'^10\.\d{4,9}/[-._;()/:A-Z0-9]+$'
    return bool(re.match(doi_pattern, doi, re.IGNORECASE))

def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

def validate_url(url: str) -> bool:
    """Validate URL format"""
    if not url:
        return False
    
    url_pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*\??[/\w\.-=&%]*$'
    return bool(re.match(url_pattern, url))

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    if not phone:
        return False
    
    # International phone number pattern
    phone_pattern = r'^\+?[\d\s\-\(\)]{10,}$'
    return bool(re.match(phone_pattern, phone))

def validate_date_format(date_string: str, format: str = "%Y-%m-%d") -> bool:
    """Validate date format"""
    try:
        datetime.strptime(date_string, format)
        return True
    except (ValueError, TypeError):
        return False

def validate_file_size(file: UploadFile, max_size_mb: int = 10) -> bool:
    """Validate file size - synchronous version for backward compatibility"""
    # Note: This is a basic check. Use the async version for accurate validation.
    return file and file.filename  # Placeholder - actual validation happens in async version

async def validate_cv_content(text: str, min_length: int = 100) -> Dict[str, Any]:
    """
    Validate CV content for minimum quality standards
    """
    if not text or len(text.strip()) < min_length:
        return {
            "valid": False,
            "error": f"CV content too short. Minimum {min_length} characters required.",
            "code": "CONTENT_TOO_SHORT"
        }
    
    # Check for meaningful content (not just random characters)
    word_count = len(text.split())
    if word_count < 50:
        return {
            "valid": False,
            "error": "CV content appears to be too sparse.",
            "code": "INSUFFICIENT_CONTENT"
        }
    
    # Check for common CV sections
    cv_sections = ['experience', 'education', 'skills', 'project', 'work']
    section_count = sum(1 for section in cv_sections if section in text.lower())
    
    if section_count < 2:
        return {
            "valid": False,
            "error": "CV appears to be missing key sections (experience, education, skills).",
            "code": "MISSING_SECTIONS"
        }
    
    return {
        "valid": True,
        "word_count": word_count,
        "character_count": len(text),
        "section_coverage": section_count,
        "readability_score": await _calculate_basic_readability(text)
    }

async def _calculate_basic_readability(text: str) -> float:
    """Calculate basic readability score"""
    sentences = re.split(r'[.!?]+', text)
    words = re.findall(r'\b\w+\b', text)
    
    if not sentences or not words:
        return 0
    
    avg_sentence_length = len(words) / len(sentences)
    
    # Simple scoring based on sentence length
    if avg_sentence_length < 25:
        return 80  # Good
    elif avg_sentence_length < 35:
        return 60  # Average
    else:
        return 40  # Poor

def validate_research_keywords(keywords: List[str]) -> Dict[str, Any]:
    """
    Validate research keywords
    """
    if not keywords:
        return {
            "valid": False,
            "error": "At least one keyword is required",
            "code": "NO_KEYWORDS"
        }
    
    if len(keywords) > 20:
        return {
            "valid": False,
            "error": "Maximum 20 keywords allowed",
            "code": "TOO_MANY_KEYWORDS"
        }
    
    # Validate individual keywords
    invalid_keywords = []
    for keyword in keywords:
        if not keyword.strip():
            invalid_keywords.append("Empty keyword")
        elif len(keyword) > 50:
            invalid_keywords.append(f"Keyword too long: {keyword}")
        elif not re.match(r'^[a-zA-Z0-9\s\-_]+$', keyword):
            invalid_keywords.append(f"Invalid characters in keyword: {keyword}")
    
    if invalid_keywords:
        return {
            "valid": False,
            "error": "Invalid keywords found",
            "code": "INVALID_KEYWORDS",
            "details": invalid_keywords
        }
    
    return {
        "valid": True,
        "keyword_count": len(keywords),
        "average_length": sum(len(k) for k in keywords) / len(keywords)
    }

def validate_academic_credentials(credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate academic credentials
    """
    errors = []
    
    # Validate institution
    institution = credentials.get('institution', '').strip()
    if not institution or len(institution) < 2:
        errors.append("Institution name is required and must be at least 2 characters")
    
    # Validate degree
    degree = credentials.get('degree', '').strip()
    if not degree or len(degree) < 2:
        errors.append("Degree name is required and must be at least 2 characters")
    
    # Validate year
    year = credentials.get('year')
    if year:
        try:
            year_int = int(year)
            current_year = datetime.now().year
            if year_int < 1900 or year_int > current_year + 5:
                errors.append(f"Year must be between 1900 and {current_year + 5}")
        except (ValueError, TypeError):
            errors.append("Year must be a valid number")
    
    # Validate GPA if provided
    gpa = credentials.get('gpa')
    if gpa is not None:
        try:
            gpa_float = float(gpa)
            if gpa_float < 0.0 or gpa_float > 4.0:
                errors.append("GPA must be between 0.0 and 4.0")
        except (ValueError, TypeError):
            errors.append("GPA must be a valid number")
    
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "code": "INVALID_CREDENTIALS"
        }
    
    return {
        "valid": True,
        "institution": institution,
        "degree": degree,
        "has_year": year is not None,
        "has_gpa": gpa is not None
    }

# Utility function for CV parsing validation
async def validate_parsed_cv_data(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate parsed CV data structure and content
    """
    required_fields = ['text', 'sections', 'metadata']
    missing_fields = [field for field in required_fields if field not in parsed_data]
    
    if missing_fields:
        return {
            "valid": False,
            "error": f"Missing required fields: {', '.join(missing_fields)}",
            "code": "MISSING_FIELDS"
        }
    
    # Validate text content
    text = parsed_data.get('text', '')
    if not text or len(text.strip()) < 50:
        return {
            "valid": False,
            "error": "Parsed text is too short or empty",
            "code": "INSUFFICIENT_TEXT"
        }
    
    # Validate sections
    sections = parsed_data.get('sections', {})
    if not sections or len(sections) == 0:
        return {
            "valid": False,
            "error": "No sections extracted from CV",
            "code": "NO_SECTIONS"
        }
    
    # Calculate quality score
    quality_score = await _calculate_parsing_quality(parsed_data)
    
    return {
        "valid": True,
        "quality_score": quality_score,
        "section_count": len(sections),
        "text_length": len(text),
        "word_count": len(text.split()),
        "status": "high_quality" if quality_score >= 70 else "medium_quality" if quality_score >= 50 else "low_quality"
    }

async def _calculate_parsing_quality(parsed_data: Dict[str, Any]) -> float:
    """Calculate parsing quality score (0-100)"""
    score = 0
    
    # Text length factor
    text_length = len(parsed_data.get('text', ''))
    if text_length > 1000:
        score += 30
    elif text_length > 500:
        score += 20
    elif text_length > 100:
        score += 10
    
    # Section coverage factor
    sections = parsed_data.get('sections', {})
    section_count = len(sections)
    if section_count >= 5:
        score += 30
    elif section_count >= 3:
        score += 20
    elif section_count >= 1:
        score += 10
    
    # Key section presence
    key_sections = ['education', 'experience', 'skills']
    key_section_count = sum(1 for section in key_sections if section in sections)
    score += key_section_count * 10
    
    # Metadata factor
    metadata = parsed_data.get('metadata', {})
    if metadata.get('pages', 0) > 0:
        score += 10
    
    return min(100, score)

# Export all validation functions
__all__ = [
    'validate_file',
    'validate_doi',
    'validate_email',
    'validate_url',
    'validate_phone',
    'validate_date_format',
    'validate_file_size',
    'validate_cv_content',
    'validate_research_keywords',
    'validate_academic_credentials',
    'validate_parsed_cv_data',
    'FileValidationError'
]