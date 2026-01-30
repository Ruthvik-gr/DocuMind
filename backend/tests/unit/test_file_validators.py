"""
Unit tests for file validators.
"""
import pytest
import io
from fastapi import UploadFile
from starlette.datastructures import Headers
from app.utils.file_validators import validate_file_type, validate_file_size
from app.utils.exceptions import InvalidFileError
from app.core.constants import FileType


def create_upload_file(filename: str, content: bytes, content_type: str = None) -> UploadFile:
    """Helper to create UploadFile with proper headers for testing."""
    headers = Headers({"content-type": content_type}) if content_type else Headers({})
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content),
        headers=headers
    )


class TestFileValidators:
    """Test file validation functions."""

    def test_validate_pdf_type(self):
        """Test PDF file type validation."""
        file = create_upload_file("test.pdf", b"test content", "application/pdf")
        result = validate_file_type(file)
        assert result == FileType.PDF

    def test_validate_audio_type(self):
        """Test audio file type validation."""
        file = create_upload_file("test.mp3", b"test content", "audio/mpeg")
        result = validate_file_type(file)
        assert result == FileType.AUDIO

    def test_validate_video_type(self):
        """Test video file type validation."""
        file = create_upload_file("test.mp4", b"test content", "video/mp4")
        result = validate_file_type(file)
        assert result == FileType.VIDEO

    def test_validate_invalid_type(self):
        """Test invalid file type rejection."""
        file = create_upload_file("test.txt", b"test content", "text/plain")
        with pytest.raises(InvalidFileError):
            validate_file_type(file)

    def test_validate_file_size_valid(self):
        """Test file size validation with valid size."""
        content = b"test content"
        file = create_upload_file("test.pdf", content)
        size = validate_file_size(file)
        assert size == len(content)

    def test_validate_file_size_too_large(self):
        """Test file size validation with file too large."""
        # Create a file larger than 200MB
        large_content = b"x" * (201 * 1024 * 1024)
        file = create_upload_file("large.pdf", large_content)
        with pytest.raises(InvalidFileError):
            validate_file_size(file)
