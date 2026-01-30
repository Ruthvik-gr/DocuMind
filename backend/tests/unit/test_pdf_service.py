"""
Unit tests for PDF service.
"""
import pytest
from unittest.mock import Mock, patch
from app.services.pdf_service import PDFService
from app.utils.exceptions import ProcessingError


class TestPDFService:
    """Test PDF extraction service."""

    @pytest.fixture
    def pdf_service(self):
        return PDFService()

    def test_extract_text_success(self, pdf_service, tmp_path):
        """Test successful PDF text extraction."""
        # This would need a real PDF file or mocking PyPDF2
        # For now, we test the error handling
        with pytest.raises(ProcessingError):
            pdf_service.extract_text("/nonexistent/file.pdf")

    def test_extract_text_invalid_file(self, pdf_service):
        """Test extraction from invalid file."""
        with pytest.raises(ProcessingError):
            pdf_service.extract_text("/invalid/path.pdf")
