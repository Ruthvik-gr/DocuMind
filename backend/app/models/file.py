"""
Database model for files collection.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.core.constants import FileType, ProcessingStatus


class ExtractedContent(BaseModel):
    """Extracted content subdocument."""
    text: str
    word_count: int
    language: str = "en"
    extraction_method: str


class FileMetadata(BaseModel):
    """File metadata subdocument."""
    duration: Optional[int] = None
    format: Optional[str] = None
    resolution: Optional[str] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None


class FileModel(BaseModel):
    """File document model."""
    file_id: str
    user_id: str
    filename: str
    file_type: FileType
    file_path: str
    file_size: int
    mime_type: str
    upload_date: datetime
    processing_status: ProcessingStatus
    processing_error: Optional[str] = None
    extracted_content: Optional[ExtractedContent] = None
    metadata: Optional[FileMetadata] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for MongoDB insertion."""
        data = self.model_dump()
        # Convert enums to strings
        data['file_type'] = self.file_type.value
        data['processing_status'] = self.processing_status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileModel":
        """Create model from MongoDB document."""
        if '_id' in data:
            del data['_id']
        return cls(**data)
