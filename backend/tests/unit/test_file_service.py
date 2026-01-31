"""
Unit tests for file service.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime
import io

from app.services.file_service import FileService
from app.core.constants import FileType, ProcessingStatus
from app.models.file import ExtractedContent, FileMetadata
from app.utils.exceptions import FileNotFoundError, DatabaseError


class TestFileService:
    """Test FileService class."""

    @pytest.fixture
    def file_service(self):
        """Create FileService instance."""
        return FileService()

    @pytest.mark.asyncio
    async def test_upload_file_success(self, file_service):
        """Test successful file upload."""
        from starlette.datastructures import Headers

        mock_file = MagicMock()
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.file = io.BytesIO(b"PDF content")

        with patch('app.services.file_service.validate_file_type', return_value=FileType.PDF), \
             patch('app.services.file_service.validate_file_size', return_value=1024), \
             patch('app.services.file_service.file_storage') as mock_storage, \
             patch('app.services.file_service.get_database') as mock_get_db:

            mock_storage.save_file.return_value = ("test-id", "/path/to/test.pdf")

            mock_collection = MagicMock()
            mock_collection.insert_one = AsyncMock()
            mock_get_db.return_value = {"files": mock_collection}

            result = await file_service.upload_file(mock_file, user_id="test-user-id")

            assert result.file_id == "test-id"
            assert result.filename == "test.pdf"
            assert result.file_type == FileType.PDF
            assert result.processing_status == ProcessingStatus.PENDING

    @pytest.mark.asyncio
    async def test_upload_file_database_error(self, file_service):
        """Test file upload with database error."""
        mock_file = MagicMock()
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        mock_file.file = io.BytesIO(b"PDF content")

        with patch('app.services.file_service.validate_file_type', return_value=FileType.PDF), \
             patch('app.services.file_service.validate_file_size', return_value=1024), \
             patch('app.services.file_service.file_storage') as mock_storage, \
             patch('app.services.file_service.get_database') as mock_get_db:

            mock_storage.save_file.return_value = ("test-id", "/path/to/test.pdf")
            mock_storage.delete_file = MagicMock()

            mock_collection = MagicMock()
            mock_collection.insert_one = AsyncMock(side_effect=Exception("DB error"))
            mock_get_db.return_value = {"files": mock_collection}

            with pytest.raises(DatabaseError):
                await file_service.upload_file(mock_file, user_id="test-user-id")

            mock_storage.delete_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_file_success(self, file_service):
        """Test getting file by ID."""
        with patch('app.services.file_service.get_database') as mock_get_db:
            file_data = {
                "file_id": "test-id",
                "user_id": "test-user-id",
                "filename": "test.pdf",
                "file_type": "pdf",
                "file_path": "/path/to/file",
                "file_size": 1024,
                "mime_type": "application/pdf",
                "upload_date": datetime.utcnow().isoformat(),
                "processing_status": "completed",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value=file_data)
            mock_get_db.return_value = {"files": mock_collection}

            result = await file_service.get_file("test-id")

            assert result.file_id == "test-id"
            assert result.filename == "test.pdf"

    @pytest.mark.asyncio
    async def test_get_file_not_found(self, file_service):
        """Test getting non-existent file."""
        with patch('app.services.file_service.get_database') as mock_get_db:
            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_get_db.return_value = {"files": mock_collection}

            with pytest.raises(FileNotFoundError):
                await file_service.get_file("non-existent")

    @pytest.mark.asyncio
    async def test_update_processing_status(self, file_service):
        """Test updating processing status."""
        with patch('app.services.file_service.get_database') as mock_get_db:
            mock_collection = MagicMock()
            mock_collection.update_one = AsyncMock()
            mock_get_db.return_value = {"files": mock_collection}

            await file_service.update_processing_status("test-id", ProcessingStatus.COMPLETED)

            mock_collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_processing_status_with_error(self, file_service):
        """Test updating processing status with error message."""
        with patch('app.services.file_service.get_database') as mock_get_db:
            mock_collection = MagicMock()
            mock_collection.update_one = AsyncMock()
            mock_get_db.return_value = {"files": mock_collection}

            await file_service.update_processing_status(
                "test-id",
                ProcessingStatus.FAILED,
                error="Processing failed"
            )

            mock_collection.update_one.assert_called_once()
            call_args = mock_collection.update_one.call_args
            assert "processing_error" in call_args[0][1]["$set"]

    @pytest.mark.asyncio
    async def test_update_extracted_content(self, file_service):
        """Test updating extracted content."""
        with patch('app.services.file_service.get_database') as mock_get_db:
            mock_collection = MagicMock()
            mock_collection.update_one = AsyncMock()
            mock_get_db.return_value = {"files": mock_collection}

            extracted_content = ExtractedContent(
                text="Extracted text",
                word_count=2,
                language="en",
                extraction_method="PyPDF2"
            )

            await file_service.update_extracted_content("test-id", extracted_content)

            mock_collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_metadata(self, file_service):
        """Test updating file metadata."""
        with patch('app.services.file_service.get_database') as mock_get_db:
            mock_collection = MagicMock()
            mock_collection.update_one = AsyncMock()
            mock_get_db.return_value = {"files": mock_collection}

            metadata = FileMetadata(
                duration=120,
                format="mp3",
                sample_rate=44100
            )

            await file_service.update_metadata("test-id", metadata)

            mock_collection.update_one.assert_called_once()
