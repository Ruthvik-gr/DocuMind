"""
Pydantic schemas for file-related endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.core.constants import FileType, ProcessingStatus


class ExtractedContentSchema(BaseModel):
    """Schema for extracted content."""
    text: str
    word_count: int
    language: str = "en"
    extraction_method: str


class FileMetadataSchema(BaseModel):
    """Schema for file metadata."""
    duration: Optional[int] = None  # For audio/video in seconds
    format: Optional[str] = None
    resolution: Optional[str] = None  # For video
    sample_rate: Optional[int] = None  # For audio
    channels: Optional[int] = None  # For audio


class FileUploadResponse(BaseModel):
    """Response schema for file upload."""
    file_id: str
    filename: str
    file_type: FileType
    file_size: int
    processing_status: ProcessingStatus
    upload_date: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "document.pdf",
                "file_type": "pdf",
                "file_size": 1048576,
                "processing_status": "pending",
                "upload_date": "2026-01-29T10:00:00"
            }
        }


class FileDetailResponse(BaseModel):
    """Detailed response schema for file information."""
    file_id: str
    filename: str
    file_type: FileType
    file_size: int
    mime_type: str
    processing_status: ProcessingStatus
    processing_error: Optional[str] = None
    extracted_content: Optional[ExtractedContentSchema] = None
    metadata: Optional[FileMetadataSchema] = None
    upload_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "document.pdf",
                "file_type": "pdf",
                "file_size": 1048576,
                "mime_type": "application/pdf",
                "processing_status": "completed",
                "processing_error": None,
                "extracted_content": {
                    "text": "Sample extracted text...",
                    "word_count": 500,
                    "language": "en",
                    "extraction_method": "PyPDF2"
                },
                "metadata": None,
                "upload_date": "2026-01-29T10:00:00",
                "created_at": "2026-01-29T10:00:00",
                "updated_at": "2026-01-29T10:05:00"
            }
        }
