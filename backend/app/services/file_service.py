"""
File management service.
"""
from fastapi import UploadFile
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from app.core.database import get_database
from app.core.storage import file_storage
from app.core.constants import (
    FileType,
    ProcessingStatus,
    COLLECTION_FILES
)
from app.models.file import FileModel, ExtractedContent, FileMetadata
from app.utils.file_validators import validate_file_type, validate_file_size
from app.utils.exceptions import FileNotFoundError, DatabaseError
from app.services.cloudinary_service import cloudinary_service

logger = logging.getLogger(__name__)


class FileService:
    """Service for file operations."""

    async def upload_file(self, file: UploadFile, user_id: str) -> FileModel:
        """
        Upload and store a file.

        Args:
            file: Uploaded file object
            user_id: ID of the user uploading the file

        Returns:
            FileModel with file metadata

        Raises:
            InvalidFileError: If file validation fails
            DatabaseError: If database operation fails
        """
        # Validate file
        file_type = validate_file_type(file)
        file_size = validate_file_size(file)

        # Save file to storage
        file_id, file_path = file_storage.save_file(file.file, file.filename, file_type)

        # Create file model
        file_model = FileModel(
            file_id=file_id,
            user_id=user_id,
            filename=file.filename,
            file_type=file_type,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type,
            upload_date=datetime.utcnow(),
            processing_status=ProcessingStatus.PENDING
        )

        # Store in database
        db = get_database()
        try:
            await db[COLLECTION_FILES].insert_one(file_model.to_dict())
            logger.info(f"File uploaded successfully: {file_id}")
            return file_model
        except Exception as e:
            logger.error(f"Failed to store file metadata: {e}")
            # Clean up stored file
            file_storage.delete_file(file_path)
            raise DatabaseError(f"Failed to store file metadata: {e}")

    async def get_file(self, file_id: str, user_id: str = None) -> FileModel:
        """
        Get file by ID.

        Args:
            file_id: File ID
            user_id: Optional user ID to filter by ownership

        Returns:
            FileModel

        Raises:
            FileNotFoundError: If file not found
        """
        db = get_database()
        query = {"file_id": file_id}
        if user_id:
            query["user_id"] = user_id

        file_data = await db[COLLECTION_FILES].find_one(query)

        if not file_data:
            raise FileNotFoundError(f"File not found: {file_id}")

        return FileModel.from_dict(file_data)

    async def update_processing_status(
        self,
        file_id: str,
        status: ProcessingStatus,
        error: Optional[str] = None
    ):
        """Update file processing status."""
        db = get_database()
        update_data = {
            "processing_status": status.value,
            "updated_at": datetime.utcnow()
        }

        if error:
            update_data["processing_error"] = error

        await db[COLLECTION_FILES].update_one(
            {"file_id": file_id},
            {"$set": update_data}
        )
        logger.info(f"Updated file {file_id} status to {status.value}")

    async def update_extracted_content(
        self,
        file_id: str,
        extracted_content: ExtractedContent
    ):
        """Update file with extracted content."""
        db = get_database()
        await db[COLLECTION_FILES].update_one(
            {"file_id": file_id},
            {
                "$set": {
                    "extracted_content": extracted_content.model_dump(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"Updated extracted content for file {file_id}")

    async def update_metadata(
        self,
        file_id: str,
        metadata: FileMetadata
    ):
        """Update file metadata."""
        db = get_database()
        await db[COLLECTION_FILES].update_one(
            {"file_id": file_id},
            {
                "$set": {
                    "metadata": metadata.model_dump(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

    async def update_cloudinary_info(
        self,
        file_id: str,
        cloudinary_info: Dict[str, Any]
    ):
        """Update file with Cloudinary information."""
        db = get_database()
        await db[COLLECTION_FILES].update_one(
            {"file_id": file_id},
            {
                "$set": {
                    "cloudinary_url": cloudinary_info.get("cloudinary_url"),
                    "cloudinary_public_id": cloudinary_info.get("cloudinary_public_id"),
                    "cloudinary_resource_type": cloudinary_info.get("cloudinary_resource_type"),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"Updated Cloudinary info for file {file_id}")

    async def list_files(self, user_id: str) -> list:
        """
        List all files for a user.

        Args:
            user_id: User ID to filter files

        Returns:
            List of FileModel objects
        """
        db = get_database()
        cursor = db[COLLECTION_FILES].find(
            {"user_id": user_id}
        ).sort("created_at", -1)

        files = []
        async for file_data in cursor:
            files.append(FileModel.from_dict(file_data))

        return files

    async def delete_file(self, file_id: str, user_id: str) -> bool:
        """
        Delete a file by ID.

        Args:
            file_id: File ID to delete
            user_id: User ID for ownership verification

        Returns:
            True if deleted successfully

        Raises:
            FileNotFoundError: If file not found
        """
        db = get_database()

        # Get file first to verify ownership and get path
        file_model = await self.get_file(file_id, user_id)

        # Delete from Cloudinary if uploaded there
        if file_model.cloudinary_public_id:
            try:
                await cloudinary_service.delete_file(
                    file_model.cloudinary_public_id,
                    file_model.cloudinary_resource_type or "auto"
                )
                logger.info(f"Deleted file from Cloudinary: {file_model.cloudinary_public_id}")
            except Exception as e:
                logger.warning(f"Failed to delete from Cloudinary: {e}")

        # Delete from local storage
        file_storage.delete_file(file_model.file_path)

        # Delete from database
        result = await db[COLLECTION_FILES].delete_one(
            {"file_id": file_id, "user_id": user_id}
        )

        if result.deleted_count == 0:
            raise FileNotFoundError(f"File not found: {file_id}")

        logger.info(f"Deleted file: {file_id}")
        return True


# Global service instance
file_service = FileService()
