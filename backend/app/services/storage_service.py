"""
Storage service for uploading files to S3 and File.io
"""
import asyncio
import httpx
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional
from pathlib import Path

from ..utils.config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

class StorageService:
    """Service for file storage operations"""
    
    def __init__(self):
        self.s3_client = None
        self.fileio_api_key = settings.FILEIO_API_KEY
        self.fileio_url = settings.FILEIO_API_URL
        
        # Initialize S3 client if credentials are available
        if (settings.AWS_ACCESS_KEY_ID and 
            settings.AWS_SECRET_ACCESS_KEY and 
            settings.AWS_BUCKET_NAME):
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
                logger.info("S3 client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {str(e)}")
                self.s3_client = None
    
    async def health_check(self) -> bool:
        """Check if storage services are available"""
        s3_available = await self._check_s3_health()
        fileio_available = await self._check_fileio_health()
        
        return s3_available or fileio_available
    
    async def _check_s3_health(self) -> bool:
        """Check S3 availability"""
        if not self.s3_client:
            return False
        
        try:
            # Try to list objects in bucket (limit to 1)
            self.s3_client.list_objects_v2(
                Bucket=settings.AWS_BUCKET_NAME,
                MaxKeys=1
            )
            return True
        except Exception as e:
            logger.warning(f"S3 health check failed: {str(e)}")
            return False
    
    async def _check_fileio_health(self) -> bool:
        """Check File.io availability"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.fileio_url}/")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"File.io health check failed: {str(e)}")
            return False
    
    async def upload_file(self, file_path: str, remote_filename: str) -> str:
        """
        Upload file to available storage service
        
        Args:
            file_path: Local path to file
            remote_filename: Desired filename in storage
            
        Returns:
            Public URL to access the file
        """
        try:
            logger.info(f"Uploading file: {file_path} as {remote_filename}")
            
            # Try S3 first if available
            if self.s3_client:
                try:
                    url = await self._upload_to_s3(file_path, remote_filename)
                    logger.info(f"File uploaded to S3: {url}")
                    return url
                except Exception as e:
                    logger.warning(f"S3 upload failed, trying File.io: {str(e)}")
            
            # Fallback to File.io
            if self.fileio_api_key:
                try:
                    url = await self._upload_to_fileio(file_path, remote_filename)
                    logger.info(f"File uploaded to File.io: {url}")
                    return url
                except Exception as e:
                    logger.error(f"File.io upload failed: {str(e)}")
            
            # If both fail, return local file URL as last resort
            logger.warning("All cloud uploads failed, returning local file URL")
            return f"file://{file_path}"
            
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            raise Exception(f"File upload failed: {str(e)}")
    
    async def _upload_to_s3(self, file_path: str, remote_filename: str) -> str:
        """Upload file to S3"""
        try:
            # Upload file
            self.s3_client.upload_file(
                file_path,
                settings.AWS_BUCKET_NAME,
                remote_filename,
                ExtraArgs={
                    'ContentType': 'audio/wav',
                    'ACL': 'public-read'  # Make file publicly accessible
                }
            )
            
            # Generate public URL
            url = f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{remote_filename}"
            return url
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                raise Exception(f"S3 bucket '{settings.AWS_BUCKET_NAME}' does not exist")
            elif error_code == 'AccessDenied':
                raise Exception("S3 access denied - check permissions")
            else:
                raise Exception(f"S3 upload error: {error_code}")
        except NoCredentialsError:
            raise Exception("S3 credentials not found")
        except Exception as e:
            raise Exception(f"S3 upload failed: {str(e)}")
    
    async def _upload_to_fileio(self, file_path: str, remote_filename: str) -> str:
        """Upload file to File.io"""
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                # Prepare file for upload
                with open(file_path, "rb") as f:
                    files = {
                        "file": (remote_filename, f, "audio/wav")
                    }
                    
                    # Prepare headers and data
                    headers = {}
                    data = {}
                    
                    if self.fileio_api_key:
                        headers["Authorization"] = f"Bearer {self.fileio_api_key}"
                        data["expires"] = "1w"  # File expires in 1 week
                    
                    # Upload file
                    response = await client.post(
                        f"{self.fileio_url}/",
                        files=files,
                        headers=headers,
                        data=data
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"File.io upload failed: {response.status_code} - {response.text}")
                    
                    result = response.json()
                    
                    if not result.get("success", False):
                        raise Exception(f"File.io upload failed: {result.get('message', 'Unknown error')}")
                    
                    download_url = result.get("link")
                    if not download_url:
                        raise Exception("File.io did not return download URL")
                    
                    return download_url
                    
        except Exception as e:
            raise Exception(f"File.io upload failed: {str(e)}")
    
    async def delete_file(self, file_url: str) -> bool:
        """
        Delete file from storage (if supported)
        
        Args:
            file_url: URL of file to delete
            
        Returns:
            True if deletion was successful or not needed
        """
        try:
            if file_url.startswith("file://"):
                # Local file - delete from filesystem
                local_path = file_url.replace("file://", "")
                if Path(local_path).exists():
                    Path(local_path).unlink()
                    logger.info(f"Deleted local file: {local_path}")
                return True
            
            elif "s3.amazonaws.com" in file_url or "s3." in file_url:
                # S3 file - extract key and delete
                return await self._delete_from_s3(file_url)
            
            else:
                # File.io or other service - deletion not typically supported
                logger.info(f"Deletion not supported for URL: {file_url}")
                return True
                
        except Exception as e:
            logger.warning(f"File deletion failed: {str(e)}")
            return False
    
    async def _delete_from_s3(self, file_url: str) -> bool:
        """Delete file from S3"""
        try:
            if not self.s3_client:
                return False
            
            # Extract object key from URL
            # URL format: https://bucket.s3.region.amazonaws.com/key
            parts = file_url.split('/')
            object_key = '/'.join(parts[3:])  # Everything after domain
            
            self.s3_client.delete_object(
                Bucket=settings.AWS_BUCKET_NAME,
                Key=object_key
            )
            
            logger.info(f"Deleted S3 object: {object_key}")
            return True
            
        except Exception as e:
            logger.warning(f"S3 deletion failed: {str(e)}")
            return False
    
    async def get_file_info(self, file_url: str) -> Optional[dict]:
        """
        Get information about uploaded file
        
        Args:
            file_url: URL of the file
            
        Returns:
            Dictionary with file information or None
        """
        try:
            if file_url.startswith("file://"):
                # Local file
                local_path = file_url.replace("file://", "")
                path = Path(local_path)
                if path.exists():
                    return {
                        "size": path.stat().st_size,
                        "exists": True,
                        "type": "local"
                    }
            
            elif "s3.amazonaws.com" in file_url:
                # S3 file
                return await self._get_s3_file_info(file_url)
            
            else:
                # External URL - try HEAD request
                async with httpx.AsyncClient() as client:
                    response = await client.head(file_url)
                    if response.status_code == 200:
                        return {
                            "size": int(response.headers.get("content-length", 0)),
                            "exists": True,
                            "type": "external",
                            "content_type": response.headers.get("content-type")
                        }
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get file info: {str(e)}")
            return None
    
    async def _get_s3_file_info(self, file_url: str) -> Optional[dict]:
        """Get S3 file information"""
        try:
            if not self.s3_client:
                return None
            
            # Extract object key from URL
            parts = file_url.split('/')
            object_key = '/'.join(parts[3:])
            
            response = self.s3_client.head_object(
                Bucket=settings.AWS_BUCKET_NAME,
                Key=object_key
            )
            
            return {
                "size": response.get("ContentLength", 0),
                "exists": True,
                "type": "s3",
                "content_type": response.get("ContentType"),
                "last_modified": response.get("LastModified")
            }
            
        except Exception as e:
            logger.warning(f"Failed to get S3 file info: {str(e)}")
            return None
