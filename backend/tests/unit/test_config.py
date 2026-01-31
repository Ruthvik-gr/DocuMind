"""
Unit tests for configuration module.
"""
import pytest
from unittest.mock import patch
import os


class TestConfig:
    """Test configuration module."""

    def test_get_settings_cached(self):
        """Test that settings are cached."""
        from app.config import get_settings

        settings1 = get_settings()
        settings2 = get_settings()

        # Should return the same cached instance
        assert settings1 is settings2

    def test_settings_defaults(self):
        """Test default settings values."""
        with patch.dict(os.environ, {
            'GROQ_API_KEY': 'test-key',
            'MONGODB_URL': 'mongodb://localhost:27017/test',
            'ENVIRONMENT': 'development'
        }, clear=False):
            from app.config import Settings

            settings = Settings()

            assert settings.APP_NAME == "DocuMind"
            assert settings.ENVIRONMENT in ["development", "test"]  # Allow test environment
            assert settings.DEBUG is True
            assert settings.GROQ_MODEL == "llama-3.3-70b-versatile"
            assert settings.GROQ_TEMPERATURE == 0.3
            assert settings.MAX_FILE_SIZE_MB == 200


class TestExceptions:
    """Test custom exceptions."""

    def test_documind_exception(self):
        """Test base exception."""
        from app.utils.exceptions import DocuMindException

        exc = DocuMindException("Test error")
        assert str(exc) == "Test error"

    def test_invalid_file_error(self):
        """Test InvalidFileError."""
        from app.utils.exceptions import InvalidFileError

        exc = InvalidFileError("Invalid file type")
        assert str(exc) == "Invalid file type"
        assert isinstance(exc, Exception)

    def test_file_not_found_error(self):
        """Test FileNotFoundError."""
        from app.utils.exceptions import FileNotFoundError

        exc = FileNotFoundError("File not found")
        assert str(exc) == "File not found"

    def test_processing_error(self):
        """Test ProcessingError."""
        from app.utils.exceptions import ProcessingError

        exc = ProcessingError("Processing failed")
        assert str(exc) == "Processing failed"

    def test_database_error(self):
        """Test DatabaseError."""
        from app.utils.exceptions import DatabaseError

        exc = DatabaseError("Database connection failed")
        assert str(exc) == "Database connection failed"

    def test_external_api_error(self):
        """Test ExternalAPIError."""
        from app.utils.exceptions import ExternalAPIError

        exc = ExternalAPIError("API call failed")
        assert str(exc) == "API call failed"

    def test_exception_inheritance(self):
        """Test exception inheritance."""
        from app.utils.exceptions import (
            DocuMindException,
            InvalidFileError,
            FileNotFoundError,
            ProcessingError,
            DatabaseError,
            ExternalAPIError
        )

        assert issubclass(InvalidFileError, DocuMindException)
        assert issubclass(FileNotFoundError, DocuMindException)
        assert issubclass(ProcessingError, DocuMindException)
        assert issubclass(DatabaseError, DocuMindException)
        assert issubclass(ExternalAPIError, DocuMindException)
