"""
Unit tests for various services.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime


class TestLangChainService:
    """Test LangChain service."""

    def test_service_import(self):
        """Test that service can be imported."""
        from app.services.langchain_service import langchain_service
        assert langchain_service is not None

    def test_vector_stores_dict(self):
        """Test vector stores dictionary exists."""
        from app.services.langchain_service import langchain_service
        assert hasattr(langchain_service, 'vector_stores')
        assert isinstance(langchain_service.vector_stores, dict)


class TestSummaryService:
    """Test summary service."""

    def test_service_import(self):
        """Test that service can be imported."""
        from app.services.summary_service import summary_service
        assert summary_service is not None

    def test_service_has_client(self):
        """Test summary service has groq client."""
        from app.services.summary_service import summary_service
        assert hasattr(summary_service, 'client')


class TestTimestampService:
    """Test timestamp service."""

    def test_service_import(self):
        """Test that service can be imported."""
        from app.services.timestamp_service import timestamp_service
        assert timestamp_service is not None


class TestTranscriptionService:
    """Test transcription service."""

    def test_service_import(self):
        """Test that service can be imported."""
        from app.services.transcription_service import transcription_service
        assert transcription_service is not None


class TestPdfService:
    """Test PDF service."""

    def test_service_import(self):
        """Test that service can be imported."""
        from app.services.pdf_service import pdf_service
        assert pdf_service is not None

    def test_extract_text_valid_pdf(self):
        """Test text extraction from valid PDF."""
        import io
        from PyPDF2 import PdfWriter

        # Create a simple PDF in memory
        pdf_writer = PdfWriter()
        pdf_writer.add_blank_page(width=612, height=792)

        pdf_buffer = io.BytesIO()
        pdf_writer.write(pdf_buffer)
        pdf_buffer.seek(0)

        from app.services.pdf_service import pdf_service

        # Write the PDF to a temp file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_buffer.read())
            temp_path = f.name

        try:
            result = pdf_service.extract_text(temp_path)
            # Blank PDF will have empty or minimal text
            assert result is not None
            assert result.extraction_method == "PyPDF2"
        finally:
            import os
            os.unlink(temp_path)


class TestFileService:
    """Test file service."""

    def test_service_import(self):
        """Test that service can be imported."""
        from app.services.file_service import file_service
        assert file_service is not None
