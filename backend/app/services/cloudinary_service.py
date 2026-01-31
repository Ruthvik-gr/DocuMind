"""
Cloudinary service for file storage.
"""
import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import BinaryIO, Optional, Dict, Any
import logging
import os

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
        file_path: str,
        file_id: str,
        file_type: FileType,
        original_filename: str
    ) -> Dict[str, Any]:
        """
        Upload a file to Cloudinary.

        Args:
            file_path: Local path to the file
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

            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file_path,
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


# Global service instance
cloudinary_service = CloudinaryService()
