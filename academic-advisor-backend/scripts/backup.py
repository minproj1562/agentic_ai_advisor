"""
Automated backup script for Firebase and database
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
import boto3
import gzip
import shutil

from app.core.firebase_admin import firebase_manager
from app.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)

class BackupManager:
    """
    Manage backups for Firebase and database
    """
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # S3 client for remote backup
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.s3_bucket = settings.BACKUP_S3_BUCKET
    
    async def backup_firebase(self):
        """
        Backup Firebase data
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"firebase_backup_{timestamp}.json"
            
            logger.info("Starting Firebase backup...")
            
            # Collections to backup
            collections = [
                'students',
                'faculty',
                'courses',
                'resources',
                'announcements'
            ]
            
            backup_data = {}
            
            for collection in collections:
                logger.info(f"Backing up collection: {collection}")
                
                # Get all documents
                documents = await firebase_manager.get_collection(
                    collection=collection
                )
                
                backup_data[collection] = documents
                
                # Also backup subcollections for students
                if collection == 'students':
                    for student in documents:
                        student_id = student['id']
                        
                        # Backup performance data
                        performance = await firebase_manager.get_collection(
                            collection=f'students/{student_id}/performance'
                        )
                        backup_data[f'students/{student_id}/performance'] = performance
                        
                        # Backup weaknesses
                        weaknesses = await firebase_manager.get_collection(
                            collection=f'students/{student_id}/weaknesses'
                        )
                        backup_data[f'students/{student_id}/weaknesses'] = weaknesses
            
            # Save to file
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            # Compress
            compressed_file = f"{backup_file}.gz"
            with open(backup_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Upload to S3
            await self.upload_to_s3(compressed_file)
            
            # Clean up local file
            os.remove(backup_file)
            
            logger.info(f"Firebase backup completed: {compressed_file}")
            
            return compressed_file
            
        except Exception as e:
            logger.error(f"Firebase backup failed: {str(e)}")
            raise
    
    async def backup_database(self):
        """
        Backup PostgreSQL database
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"postgres_backup_{timestamp}.sql"
            
            logger.info("Starting PostgreSQL backup...")
            
            # Use pg_dump
            import subprocess
            
            db_url = settings.DATABASE_URL
            
            cmd = [
                'pg_dump',
                db_url,
                '-f', str(backup_file),
                '--verbose',
                '--no-owner',
                '--no-acl'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            # Compress
            compressed_file = f"{backup_file}.gz"
            with open(backup_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Upload to S3
            await self.upload_to_s3(compressed_file)
            
            # Clean up
            os.remove(backup_file)
            
            logger.info(f"Database backup completed: {compressed_file}")
            
            return compressed_file
            
        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}")
            raise
    
    async def upload_to_s3(self, file_path: str):
        """
        Upload backup to S3
        """
        try:
            file_name = os.path.basename(file_path)
            s3_key = f"backups/{datetime.utcnow().year}/{datetime.utcnow().month}/{file_name}"
            
            self.s3_client.upload_file(
                file_path,
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'GLACIER'
                }
            )
            
            logger.info(f"Uploaded to S3: {s3_key}")
            
        except Exception as e:
            logger.error(f"S3 upload failed: {str(e)}")
            raise
    
    async def restore_firebase(self, backup_file: str):
        """
        Restore Firebase from backup
        """
        try:
            logger.info(f"Restoring Firebase from {backup_file}")
            
            # Decompress if needed
            if backup_file.endswith('.gz'):
                import gzip
                with gzip.open(backup_file, 'rt') as f:
                    backup_data = json.load(f)
            else:
                with open(backup_file, 'r') as f:
                    backup_data = json.load(f)
            
            # Restore each collection
            for collection_path, documents in backup_data.items():
                logger.info(f"Restoring {collection_path}")
                
                for doc in documents:
                    doc_id = doc.pop('id', None)
                    
                    await firebase_manager.create_document(
                        collection=collection_path,
                        document_id=doc_id,
                        data=doc
                    )
            
            logger.info("Firebase restore completed")
            
        except Exception as e:
            logger.error(f"Firebase restore failed: {str(e)}")
            raise
    
    async def cleanup_old_backups(self, days: int = 30):
        """
        Clean up old backups
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            for backup_file in self.backup_dir.glob("*.gz"):
                # Get file modification time
                mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                if mtime < cutoff_date:
                    logger.info(f"Deleting old backup: {backup_file}")
                    backup_file.unlink()
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")

async def main():
    """
    Main backup routine
    """
    manager = BackupManager()
    
    # Perform backups
    await manager.backup_firebase()
    
    if settings.DATABASE_URL:
        await manager.backup_database()
    
    # Cleanup old backups
    await manager.cleanup_old_backups(days=30)

if __name__ == "__main__":
    asyncio.run(main())