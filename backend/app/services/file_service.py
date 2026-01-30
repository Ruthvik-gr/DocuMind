"""
File management service.
"""
from fastapi import UploadFile
from datetime import datetime
from typing import Optional
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

logger = logging.getLogger(__name__)


class FileService:
    """Service for file operations."""

    async def upload_file(self, file: UploadFile) -> FileModel:
        """
        Upload and store a file.

        Args:
            file: Uploaded file object

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

    async def get_file(self, file_id: str) -> FileModel:
        """
        Get file by ID.

        Args:
            file_id: File ID

        Returns:
            FileModel

        Raises:
            FileNotFoundError: If file not found
        """
        db = get_database()
        file_data = await db[COLLECTION_FILES].find_one({"file_id": file_id})

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


# Global service instance
file_service = FileService()
