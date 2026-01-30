"""
Unit tests for file validators.
"""
import pytest
import io
from fastapi import UploadFile
from app.utils.file_validators import validate_file_type, validate_file_size
from app.utils.exceptions import InvalidFileError
from app.core.constants import FileType


class TestFileValidators:
    """Test file validation functions."""

    def test_validate_pdf_type(self):
        """Test PDF file type validation."""
        file = UploadFile(
            filename="test.pdf",
            file=io.BytesIO(b"test content"),
            content_type="application/pdf"
        )
        result = validate_file_type(file)
        assert result == FileType.PDF

    def test_validate_audio_type(self):
        """Test audio file type validation."""
        file = UploadFile(
            filename="test.mp3",
            file=io.BytesIO(b"test content"),
            content_type="audio/mpeg"
        )
        result = validate_file_type(file)
        assert result == FileType.AUDIO

    def test_validate_video_type(self):
        """Test video file type validation."""
        file = UploadFile(
            filename="test.mp4",
            file=io.BytesIO(b"test content"),
            content_type="video/mp4"
        )
        result = validate_file_type(file)
        assert result == FileType.VIDEO

    def test_validate_invalid_type(self):
        """Test invalid file type rejection."""
        file = UploadFile(
            filename="test.txt",
            file=io.BytesIO(b"test content"),
            content_type="text/plain"
        )
        with pytest.raises(InvalidFileError):
            validate_file_type(file)

    def test_validate_file_size_valid(self):
        """Test file size validation with valid size."""
        content = b"test content"
        file = UploadFile(
            filename="test.pdf",
            file=io.BytesIO(content)
        )
        size = validate_file_size(file)
        assert size == len(content)

    def test_validate_file_size_too_large(self):
        """Test file size validation with file too large."""
        # Create a file larger than 200MB
        large_content = b"x" * (201 * 1024 * 1024)
        file = UploadFile(
            filename="large.pdf",
            file=io.BytesIO(large_content)
        )
        with pytest.raises(InvalidFileError):
            validate_file_size(file)
