# app/utils/helpers.py
"""
Utility helper functions
"""

import csv
import io
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
from openpyxl import Workbook


def get_logger(name: str) -> logging.Logger:
    """
    Get configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Create handler
        handler = logging.StreamHandler()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add formatter to handler
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        # Set level
        logger.setLevel(logging.INFO)
    
    return logger


def setup_logging():
    """
    Setup application-wide logging
    """
    from app.config import settings
    
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(settings.LOG_FILE) if settings.LOG_FILE else logging.NullHandler()
        ]
    )
    
    return logging.getLogger(__name__)


def generate_csv(data: List[Dict[str, Any]]) -> io.StringIO:
    """
    Generate CSV from data
    """
    if not data:
        return io.StringIO()
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    output.seek(0)
    
    return output


def generate_excel(data: List[Dict[str, Any]]) -> io.BytesIO:
    """
    Generate Excel file from data
    """
    df = pd.DataFrame(data)
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Data', index=False)
        
        # Get workbook for styling
        workbook = writer.book
        worksheet = writer.sheets['Data']
        
        # Apply styling
        for cell in worksheet[1]:
            cell.font = cell.font.copy(bold=True)
    
    output.seek(0)
    return output


def format_datetime(dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime to string
    """
    return dt.strftime(format) if dt else ""


def parse_datetime(dt_str: str, format: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    Parse string to datetime
    """
    return datetime.strptime(dt_str, format) if dt_str else None


def calculate_percentage(value: float, total: float) -> float:
    """
    Calculate percentage safely
    """
    if total == 0:
        return 0.0
    return round((value / total) * 100, 2)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage
    """
    import re
    
    # Remove special characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return f"{name}{ext}"


def generate_unique_id() -> str:
    """
    Generate unique ID
    """
    import uuid
    return str(uuid.uuid4())


def validate_email(email: str) -> bool:
    """
    Validate email format
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt
    """
    from app.core.security import get_password_hash
    return get_password_hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    """
    from app.core.security import verify_password as verify
    return verify(plain_password, hashed_password)


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """
    Flatten nested dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Split list into chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def retry_on_failure(max_retries: int = 3, delay: int = 1):
    """
    Decorator to retry function on failure
    """
    import time
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay * (2 ** attempt))
        
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator