"""
PDF text extraction service.
"""
from PyPDF2 import PdfReader
import logging
from typing import BinaryIO

from app.utils.exceptions import ProcessingError
from app.utils.text_processors import count_words
from app.models.file import ExtractedContent

logger = logging.getLogger(__name__)


class PDFService:
    """Service for PDF text extraction."""

    def extract_text(self, file_path: str) -> ExtractedContent:
        """
        Extract text from PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            ExtractedContent with text and metadata

        Raises:
            ProcessingError: If extraction fails
        """
        try:
            reader = PdfReader(file_path)
            text_parts = []

            # Extract text from all pages
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            full_text = "\n\n".join(text_parts)

            if not full_text.strip():
                logger.warning(f"No text extracted from PDF: {file_path}")
                full_text = ""

            word_count = count_words(full_text)

            extracted_content = ExtractedContent(
                text=full_text,
                word_count=word_count,
                language="en",  # Could add language detection
                extraction_method="PyPDF2"
            )

            logger.info(f"Extracted {word_count} words from PDF: {file_path}")
            return extracted_content

        except Exception as e:
            logger.error(f"Failed to extract text from PDF {file_path}: {e}")
            raise ProcessingError(f"PDF extraction failed: {e}")


# Global service instance
pdf_service = PDFService()
