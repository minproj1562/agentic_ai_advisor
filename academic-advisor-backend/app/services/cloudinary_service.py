#academic-advisor-backend/app/services/cloudinary_service.py
import cloudinary
import cloudinary.uploader
import cloudinary.api
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Configure Cloudinary
try:
    cloudinary.config(
        cloud_name=getattr(settings, 'CLOUDINARY_CLOUD_NAME', 'your_cloud_name'),
        api_key=getattr(settings, 'CLOUDINARY_API_KEY', 'your_api_key'),
        api_secret=getattr(settings, 'CLOUDINARY_API_SECRET', 'your_api_secret'),
        secure=True
    )
    logger.info("Cloudinary configured successfully")
except Exception as e:
    logger.warning(f"Cloudinary configuration failed: {e}")

async def upload_to_cloudinary(file_content: bytes, folder: str, filename: str) -> dict:
    """
    Upload file to Cloudinary
    """
    try:
        # Upload the file
        result = cloudinary.uploader.upload(
            file_content,
            folder=folder,
            public_id=filename.split('.')[0],  # Remove extension
            resource_type="auto"  # Auto-detect file type
        )
        
        logger.info(f"File uploaded to Cloudinary: {result['secure_url']}")
        return result
        
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        raise Exception(f"Failed to upload file to Cloudinary: {str(e)}")

async def delete_from_cloudinary(public_id: str) -> bool:
    """
    Delete file from Cloudinary
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get('result') == 'ok'
    except Exception as e:
        logger.error(f"Cloudinary delete failed: {e}")
        return False

async def get_cloudinary_url(public_id: str, transformations: dict = None) -> str:
    """
    Generate Cloudinary URL with optional transformations
    """
    try:
        url = cloudinary.CloudinaryImage(public_id).build_url(**transformations if transformations else {})
        return url
    except Exception as e:
        logger.error(f"Cloudinary URL generation failed: {e}")
        return ""