"""
File storage utilities.
"""
import os
import uuid
from pathlib import Path
from typing import BinaryIO
from app.config import get_settings
from app.core.constants import FileType

settings = get_settings()


class FileStorage:
    """Handles file storage operations."""

    def __init__(self):
        self.base_path = Path(settings.STORAGE_PATH)
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure storage directories exist."""
        for file_type in FileType:
            dir_path = self.base_path / f"{file_type.value}s"
            dir_path.mkdir(parents=True, exist_ok=True)

        extracted_path = self.base_path / "extracted"
        extracted_path.mkdir(parents=True, exist_ok=True)

    def save_file(self, file: BinaryIO, filename: str, file_type: FileType) -> tuple[str, str]:
        """
        Save uploaded file to storage.

        Args:
            file: File object to save
            filename: Original filename
            file_type: Type of file (pdf, audio, video)

        Returns:
            Tuple of (file_id, file_path)
        """
        file_id = str(uuid.uuid4())
        file_extension = Path(filename).suffix
        stored_filename = f"{file_id}{file_extension}"

        # Determine storage directory based on file type
        storage_dir = self.base_path / f"{file_type.value}s"
        file_path = storage_dir / stored_filename

        # Save file
        with open(file_path, "wb") as f:
            f.write(file.read())

        return file_id, str(file_path)

    def get_file_path(self, file_id: str, file_type: FileType, extension: str) -> Path:
        """Get full path for a file."""
        storage_dir = self.base_path / f"{file_type.value}s"
        return storage_dir / f"{file_id}{extension}"

    def delete_file(self, file_path: str):
        """Delete a file from storage."""
        try:
            Path(file_path).unlink(missing_ok=True)
        except Exception as e:
            # Log error but don't raise
            pass


# Global storage instance
file_storage = FileStorage()
