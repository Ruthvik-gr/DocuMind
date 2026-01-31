"""
Cloudinary service for file storage.
"""
import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import BinaryIO, Optional, Dict, Any
import logging
import os
import tempfile
import requests

from app.config import get_settings
from app.core.constants import FileType

logger = logging.getLogger(__name__)
settings = get_settings()

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)


class CloudinaryService:
    """Service for Cloudinary file operations."""

    def __init__(self):
        self.configured = bool(
            settings.CLOUDINARY_CLOUD_NAME and
            settings.CLOUDINARY_API_KEY and
            settings.CLOUDINARY_API_SECRET
        )
        if not self.configured:
            logger.warning("Cloudinary is not configured. Files will be stored locally.")

    def is_configured(self) -> bool:
        """Check if Cloudinary is properly configured."""
        return self.configured

    async def upload_file(
        self,
        file_buffer: BinaryIO,
        file_id: str,
        file_type: FileType,
        original_filename: str
    ) -> Dict[str, Any]:
        """
        Upload a file to Cloudinary from file buffer (no local storage).

        Args:
            file_buffer: File buffer/stream to upload
            file_id: Unique file ID
            file_type: Type of file (pdf, audio, video)
            original_filename: Original filename

        Returns:
            Dict with cloudinary_url and cloudinary_public_id
        """
        if not self.configured:
            raise ValueError("Cloudinary is not configured")

        try:
            # Determine resource type based on file type
            if file_type == FileType.PDF:
                resource_type = "raw"
            elif file_type == FileType.VIDEO:
                resource_type = "video"
            elif file_type == FileType.AUDIO:
                resource_type = "video"  # Cloudinary treats audio as video
            else:
                resource_type = "auto"

            # Create public_id with folder structure
            folder = f"documind/{file_type.value}s"
            public_id = f"{folder}/{file_id}"

            # Upload to Cloudinary directly from buffer
            result = cloudinary.uploader.upload(
                file_buffer,
                public_id=public_id,
                resource_type=resource_type,
                overwrite=True,
                invalidate=True,
                use_filename=True,
                unique_filename=False
            )

            logger.info(f"File uploaded to Cloudinary: {result['secure_url']}")

            return {
                "cloudinary_url": result["secure_url"],
                "cloudinary_public_id": result["public_id"],
                "cloudinary_resource_type": resource_type
            }

        except Exception as e:
            logger.error(f"Failed to upload to Cloudinary: {e}")
            raise

    async def delete_file(self, public_id: str, resource_type: str = "auto") -> bool:
        """
        Delete a file from Cloudinary.

        Args:
            public_id: Cloudinary public ID
            resource_type: Resource type (raw, video, image, auto)

        Returns:
            True if deleted successfully
        """
        if not self.configured:
            return False

        try:
            result = cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type,
                invalidate=True
            )
            return result.get("result") == "ok"

        except Exception as e:
            logger.error(f"Failed to delete from Cloudinary: {e}")
            return False

    def get_streaming_url(self, public_id: str, resource_type: str = "video") -> str:
        """
        Get optimized streaming URL for media files.

        Args:
            public_id: Cloudinary public ID
            resource_type: Resource type

        Returns:
            Streaming URL
        """
        if not self.configured:
            raise ValueError("Cloudinary is not configured")

        # Generate streaming URL with optimizations
        if resource_type in ["video", "audio"]:
            url = cloudinary.CloudinaryVideo(public_id).build_url(
                resource_type="video",
                secure=True
            )
        else:
            url = cloudinary.CloudinaryResource(public_id).build_url(
                resource_type=resource_type,
                secure=True
            )

        return url

    def get_download_url(self, public_id: str, resource_type: str = "raw") -> str:
        """
        Get download URL for a file.

        Args:
            public_id: Cloudinary public ID
            resource_type: Resource type

        Returns:
            Download URL
        """
        if not self.configured:
            raise ValueError("Cloudinary is not configured")

        return cloudinary.CloudinaryResource(public_id).build_url(
            resource_type=resource_type,
            secure=True,
            flags="attachment"
        )

    async def download_to_temp(self, cloudinary_url: str, suffix: str = None) -> str:
        """
        Download a file from Cloudinary to a temporary location for processing.

        Args:
            cloudinary_url: Cloudinary URL to download
            suffix: Optional file suffix (e.g., '.pdf', '.mp4')

        Returns:
            Path to temporary file (caller must delete after use)
        """
        if not self.configured:
            raise ValueError("Cloudinary is not configured")

        try:
            # Download file from Cloudinary
            response = requests.get(cloudinary_url, stream=True)
            response.raise_for_status()

            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

            # Write content to temp file
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)

            temp_file.close()
            logger.info(f"Downloaded file to temp location: {temp_file.name}")

            return temp_file.name

        except Exception as e:
            logger.error(f"Failed to download from Cloudinary: {e}")
            raise


# Global service instance
cloudinary_service = CloudinaryService()
