# resume-service/app/services/storage_service.py
import boto3
import aioboto3
import asyncio
import os
import uuid
from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime, timedelta
import logging
from botocore.exceptions import ClientError, NoCredentialsError
import aiofiles
from pathlib import Path

logger = logging.getLogger(__name__)

class StorageService:
    """Cloud storage service for S3 and Railway integration"""
    
    def __init__(self, provider: str = "s3"):
        self.provider = provider
        self.session = None
        self.client = None
        self.bucket_name = os.getenv("STORAGE_BUCKET_NAME", "resume-service-bucket")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.endpoint_url = os.getenv("STORAGE_ENDPOINT_URL")
        
        # AWS/Railway credentials
        self.access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.session_token = os.getenv("AWS_SESSION_TOKEN")
        
        # Initialize storage client
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the storage client based on provider"""
        try:
            if self.provider == "s3":
                self._init_s3_client()
            elif self.provider == "railway":
                self._init_railway_client()
            elif self.provider == "local":
                self._init_local_client()
            else:
                raise ValueError(f"Unsupported storage provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Failed to initialize storage client: {e}")
            raise
    
    def _init_s3_client(self):
        """Initialize AWS S3 client"""
        session_kwargs = {
            'aws_access_key_id': self.access_key_id,
            'aws_secret_access_key': self.secret_access_key,
            'region_name': self.region
        }
        
        if self.session_token:
            session_kwargs['aws_session_token'] = self.session_token
        
        self.session = boto3.Session(**session_kwargs)
        self.client = self.session.client('s3')
        
        # Test connection
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Successfully connected to S3 bucket: {self.bucket_name}")
        except ClientError as e:
            logger.error(f"Failed to connect to S3 bucket: {e}")
            raise
    
    def _init_railway_client(self):
        """Initialize Railway storage client (S3-compatible)"""
        if not self.endpoint_url:
            raise ValueError("Railway endpoint URL is required")
        
        session_kwargs = {
            'aws_access_key_id': self.access_key_id,
            'aws_secret_access_key': self.secret_access_key,
            'region_name': self.region
        }
        
        self.session = boto3.Session(**session_kwargs)
        self.client = self.session.client(
            's3',
            endpoint_url=self.endpoint_url,
            region_name=self.region
        )
        
        # Test connection
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Successfully connected to Railway storage: {self.bucket_name}")
        except ClientError as e:
            logger.error(f"Failed to connect to Railway storage: {e}")
            raise
    
    def _init_local_client(self):
        """Initialize local file storage"""
        self.local_storage_path = Path(os.getenv("LOCAL_STORAGE_PATH", "./local_storage"))
        self.local_storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized local storage at: {self.local_storage_path}")
    
    async def upload_file(self, file_content: bytes, filename: str, content_type: str = None) -> Dict[str, Any]:
        """Upload file to cloud storage"""
        try:
            if self.provider in ["s3", "railway"]:
                return await self._upload_to_cloud(file_content, filename, content_type)
            elif self.provider == "local":
                return await self._upload_to_local(file_content, filename, content_type)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Failed to upload file {filename}: {e}")
            raise
    
    async def _upload_to_cloud(self, file_content: bytes, filename: str, content_type: str = None) -> Dict[str, Any]:
        """Upload file to S3 or Railway"""
        # Generate unique storage key
        storage_key = self._generate_storage_key(filename)
        
        # Upload file
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=storage_key,
            Body=file_content,
            **extra_args
        )
        
        # Generate URL
        url = self._generate_url(storage_key)
        
        return {
            "storage_key": storage_key,
            "storage_url": url,
            "bucket_name": self.bucket_name,
            "region": self.region,
            "file_size": len(file_content),
            "uploaded_at": datetime.utcnow().isoformat()
        }
    
    async def _upload_to_local(self, file_content: bytes, filename: str, content_type: str = None) -> Dict[str, Any]:
        """Upload file to local storage"""
        storage_key = self._generate_storage_key(filename)
        file_path = self.local_storage_path / storage_key
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        return {
            "storage_key": storage_key,
            "storage_url": str(file_path),
            "bucket_name": "local",
            "region": "local",
            "file_size": len(file_content),
            "uploaded_at": datetime.utcnow().isoformat()
        }
    
    async def download_file(self, storage_key: str) -> bytes:
        """Download file from cloud storage"""
        try:
            if self.provider in ["s3", "railway"]:
                return await self._download_from_cloud(storage_key)
            elif self.provider == "local":
                return await self._download_from_local(storage_key)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Failed to download file {storage_key}: {e}")
            raise
    
    async def _download_from_cloud(self, storage_key: str) -> bytes:
        """Download file from S3 or Railway"""
        response = self.client.get_object(Bucket=self.bucket_name, Key=storage_key)
        return response['Body'].read()
    
    async def _download_from_local(self, storage_key: str) -> bytes:
        """Download file from local storage"""
        file_path = self.local_storage_path / storage_key
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {storage_key}")
        
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()
    
    async def delete_file(self, storage_key: str) -> bool:
        """Delete file from cloud storage"""
        try:
            if self.provider in ["s3", "railway"]:
                return await self._delete_from_cloud(storage_key)
            elif self.provider == "local":
                return await self._delete_from_local(storage_key)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Failed to delete file {storage_key}: {e}")
            return False
    
    async def _delete_from_cloud(self, storage_key: str) -> bool:
        """Delete file from S3 or Railway"""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=storage_key)
            return True
        except ClientError:
            return False
    
    async def _delete_from_local(self, storage_key: str) -> bool:
        """Delete file from local storage"""
        try:
            file_path = self.local_storage_path / storage_key
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def generate_presigned_url(self, storage_key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for file access"""
        try:
            if self.provider in ["s3", "railway"]:
                return self._generate_presigned_cloud_url(storage_key, expiration)
            elif self.provider == "local":
                return self._generate_local_url(storage_key)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {storage_key}: {e}")
            raise
    
    def _generate_presigned_cloud_url(self, storage_key: str, expiration: int) -> str:
        """Generate presigned URL for S3 or Railway"""
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': storage_key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def _generate_local_url(self, storage_key: str) -> str:
        """Generate local file URL"""
        file_path = self.local_storage_path / storage_key
        return f"file://{file_path.absolute()}"
    
    def _generate_url(self, storage_key: str) -> str:
        """Generate public URL for file"""
        if self.provider == "s3":
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{storage_key}"
        elif self.provider == "railway":
            return f"{self.endpoint_url}/{self.bucket_name}/{storage_key}"
        elif self.provider == "local":
            return f"file://{self.local_storage_path / storage_key}"
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _generate_storage_key(self, filename: str) -> str:
        """Generate unique storage key for file"""
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        unique_id = str(uuid.uuid4())
        extension = Path(filename).suffix
        
        return f"resumes/{timestamp}/{unique_id}{extension}"
    
    async def list_files(self, prefix: str = "", max_keys: int = 1000) -> List[Dict[str, Any]]:
        """List files in storage"""
        try:
            if self.provider in ["s3", "railway"]:
                return await self._list_cloud_files(prefix, max_keys)
            elif self.provider == "local":
                return await self._list_local_files(prefix, max_keys)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    async def _list_cloud_files(self, prefix: str, max_keys: int) -> List[Dict[str, Any]]:
        """List files in S3 or Railway"""
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        "key": obj['Key'],
                        "size": obj['Size'],
                        "last_modified": obj['LastModified'].isoformat(),
                        "url": self._generate_url(obj['Key'])
                    })
            
            return files
        except Exception as e:
            logger.error(f"Failed to list cloud files: {e}")
            return []
    
    async def _list_local_files(self, prefix: str, max_keys: int) -> List[Dict[str, Any]]:
        """List files in local storage"""
        try:
            files = []
            prefix_path = self.local_storage_path / prefix
            
            if prefix_path.exists():
                for file_path in prefix_path.rglob("*"):
                    if file_path.is_file():
                        stat = file_path.stat()
                        files.append({
                            "key": str(file_path.relative_to(self.local_storage_path)),
                            "size": stat.st_size,
                            "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "url": f"file://{file_path.absolute()}"
                        })
                        
                        if len(files) >= max_keys:
                            break
            
            return files
        except Exception as e:
            logger.error(f"Failed to list local files: {e}")
            return []
    
    async def get_file_info(self, storage_key: str) -> Optional[Dict[str, Any]]:
        """Get file information"""
        try:
            if self.provider in ["s3", "railway"]:
                return await self._get_cloud_file_info(storage_key)
            elif self.provider == "local":
                return await self._get_local_file_info(storage_key)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Failed to get file info for {storage_key}: {e}")
            return None
    
    async def _get_cloud_file_info(self, storage_key: str) -> Optional[Dict[str, Any]]:
        """Get file information from S3 or Railway"""
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=storage_key)
            
            return {
                "key": storage_key,
                "size": response['ContentLength'],
                "content_type": response.get('ContentType'),
                "last_modified": response['LastModified'].isoformat(),
                "etag": response['ETag'],
                "url": self._generate_url(storage_key)
            }
        except ClientError:
            return None
    
    async def _get_local_file_info(self, storage_key: str) -> Optional[Dict[str, Any]]:
        """Get file information from local storage"""
        try:
            file_path = self.local_storage_path / storage_key
            
            if not file_path.exists():
                return None
            
            stat = file_path.stat()
            
            return {
                "key": storage_key,
                "size": stat.st_size,
                "content_type": self._guess_content_type(file_path),
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "url": f"file://{file_path.absolute()}"
            }
        except Exception:
            return None
    
    def _guess_content_type(self, file_path: Path) -> str:
        """Guess content type based on file extension"""
        extension = file_path.suffix.lower()
        
        content_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif'
        }
        
        return content_types.get(extension, 'application/octet-stream')
    
    async def copy_file(self, source_key: str, destination_key: str) -> bool:
        """Copy file within storage"""
        try:
            if self.provider in ["s3", "railway"]:
                return await self._copy_cloud_file(source_key, destination_key)
            elif self.provider == "local":
                return await self._copy_local_file(source_key, destination_key)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Failed to copy file from {source_key} to {destination_key}: {e}")
            return False
    
    async def _copy_cloud_file(self, source_key: str, destination_key: str) -> bool:
        """Copy file in S3 or Railway"""
        try:
            copy_source = {'Bucket': self.bucket_name, 'Key': source_key}
            self.client.copy(copy_source, self.bucket_name, destination_key)
            return True
        except ClientError:
            return False
    
    async def _copy_local_file(self, source_key: str, destination_key: str) -> bool:
        """Copy file in local storage"""
        try:
            source_path = self.local_storage_path / source_key
            dest_path = self.local_storage_path / destination_key
            
            if not source_path.exists():
                return False
            
            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            async with aiofiles.open(source_path, 'rb') as src:
                content = await src.read()
            
            async with aiofiles.open(dest_path, 'wb') as dst:
                await dst.write(content)
            
            return True
        except Exception:
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check storage service health"""
        try:
            if self.provider in ["s3", "railway"]:
                return await self._cloud_health_check()
            elif self.provider == "local":
                return await self._local_health_check()
            else:
                return {"status": "unknown", "provider": self.provider}
                
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _cloud_health_check(self) -> Dict[str, Any]:
        """Check cloud storage health"""
        try:
            start_time = datetime.utcnow()
            self.client.head_bucket(Bucket=self.bucket_name)
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "provider": self.provider,
                "bucket": self.bucket_name,
                "region": self.region,
                "response_time": response_time,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.provider,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _local_health_check(self) -> Dict[str, Any]:
        """Check local storage health"""
        try:
            # Check if storage directory is writable
            test_file = self.local_storage_path / ".health_check"
            
            async with aiofiles.open(test_file, 'w') as f:
                await f.write("health_check")
            
            test_file.unlink()
            
            return {
                "status": "healthy",
                "provider": "local",
                "path": str(self.local_storage_path),
                "writable": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "local",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

