"""
DigitalOcean Spaces Storage Integration

This module provides file storage capabilities using DigitalOcean Spaces,
which is S3-compatible object storage. It handles file uploads, downloads,
and management for the BulletDrop platform.

Features:
- S3-compatible API integration with DigitalOcean Spaces
- Secure file upload with proper content type handling
- URL generation for public file access
- File deletion and management
- Configurable bucket and region settings

Author: BulletDrop Team
"""

import os
import uuid
from typing import Optional, BinaryIO
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
import aiofiles


class DigitalOceanSpacesStorage:
    """
    DigitalOcean Spaces storage handler for file uploads and management.

    This class provides methods to interact with DigitalOcean Spaces for
    storing and retrieving uploaded files. It uses the boto3 library with
    S3-compatible endpoints.
    """

    def __init__(self):
        """
        Initialize the DigitalOcean Spaces client.

        Raises:
            ValueError: If required environment variables are not set
        """
        self.access_key = os.getenv("DO_SPACES_KEY")
        self.secret_key = os.getenv("DO_SPACES_SECRET")
        self.endpoint_url = os.getenv("DO_SPACES_ENDPOINT")
        self.bucket_name = os.getenv("DO_SPACES_BUCKET")
        self.region = os.getenv("DO_SPACES_REGION", "nyc3")

        if not all([self.access_key, self.secret_key, self.endpoint_url, self.bucket_name]):
            raise ValueError("DigitalOcean Spaces configuration incomplete")

        # Initialize boto3 client for DigitalOcean Spaces
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region
        )

    async def upload_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        content_type: str,
        user_id: Optional[str] = None
    ) -> str:
        """
        Upload a file to DigitalOcean Spaces.

        Args:
            file_obj: Binary file object to upload
            filename: Original filename
            content_type: MIME type of the file
            user_id: Optional user ID for organizing files

        Returns:
            str: The unique key/path of the uploaded file

        Raises:
            HTTPException: If upload fails
        """
        try:
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else ''
            unique_filename = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())

            # Create file path
            file_key = f"uploads/{user_id}/{unique_filename}" if user_id else f"uploads/{unique_filename}"

            # Upload to Spaces
            self.client.upload_fileobj(
                file_obj,
                self.bucket_name,
                file_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ACL': 'public-read'  # Make files publicly accessible
                }
            )

            return file_key

        except ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file: {str(e)}"
            )

    def get_file_url(self, file_key: str) -> str:
        """
        Generate public URL for a file in DigitalOcean Spaces.

        Args:
            file_key: The key/path of the file in Spaces

        Returns:
            str: Public URL to access the file
        """
        # DigitalOcean Spaces public URL format
        base_url = self.endpoint_url.replace('https://', f'https://{self.bucket_name}.')
        return f"{base_url}/{file_key}"

    async def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from DigitalOcean Spaces.

        Args:
            file_key: The key/path of the file to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError:
            return False

    def file_exists(self, file_key: str) -> bool:
        """
        Check if a file exists in DigitalOcean Spaces.

        Args:
            file_key: The key/path of the file to check

        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError:
            return False


class LocalFileStorage:
    """
    Local file storage handler for development and fallback purposes.

    This class provides local file system storage when DigitalOcean Spaces
    is not available or configured.
    """

    def __init__(self, upload_dir: str = "/app/uploads"):
        """
        Initialize local file storage.

        Args:
            upload_dir: Directory path for storing uploaded files
        """
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)

    async def upload_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        content_type: str,
        user_id: Optional[str] = None
    ) -> str:
        """
        Upload a file to local storage.

        Args:
            file_obj: Binary file object to upload
            filename: Original filename
            content_type: MIME type of the file
            user_id: Optional user ID for organizing files

        Returns:
            str: The local path of the uploaded file
        """
        # Generate unique filename
        file_extension = filename.split('.')[-1] if '.' in filename else ''
        unique_filename = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())

        # Create user directory if specified
        if user_id:
            user_dir = os.path.join(self.upload_dir, str(user_id))
            os.makedirs(user_dir, exist_ok=True)
            file_path = os.path.join(user_dir, unique_filename)
            relative_path = f"{user_id}/{unique_filename}"
        else:
            file_path = os.path.join(self.upload_dir, unique_filename)
            relative_path = unique_filename

        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = file_obj.read()
            await f.write(content)

        return relative_path

    def get_file_url(self, file_key: str, base_url: str = "http://localhost:8000") -> str:
        """
        Generate URL for local file access.

        Args:
            file_key: The local path of the file
            base_url: Base URL of the application

        Returns:
            str: URL to access the file
        """
        return f"{base_url}/uploads/{file_key}"

    async def delete_file(self, file_key: str) -> bool:
        """
        Delete a local file.

        Args:
            file_key: The local path of the file to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            file_path = os.path.join(self.upload_dir, file_key)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False

    def file_exists(self, file_key: str) -> bool:
        """
        Check if a local file exists.

        Args:
            file_key: The local path of the file to check

        Returns:
            bool: True if file exists, False otherwise
        """
        file_path = os.path.join(self.upload_dir, file_key)
        return os.path.exists(file_path)


def get_storage_backend():
    """
    Get the appropriate storage backend based on configuration.

    Returns:
        Storage backend instance (DigitalOceanSpacesStorage or LocalFileStorage)
    """
    if all([
        os.getenv("DO_SPACES_KEY"),
        os.getenv("DO_SPACES_SECRET"),
        os.getenv("DO_SPACES_ENDPOINT"),
        os.getenv("DO_SPACES_BUCKET")
    ]):
        return DigitalOceanSpacesStorage()
    else:
        return LocalFileStorage()