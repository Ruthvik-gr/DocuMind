"""
Pydantic schemas for timestamp-related endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TimestampEntrySchema(BaseModel):
    """Schema for a single timestamp entry."""
    timestamp_entry_id: str
    time: int = Field(..., ge=0, description="Time in seconds")
    topic: str
    description: str
    keywords: List[str] = []
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp_entry_id": "ts-entry-123",
                "time": 120,
                "topic": "Introduction to AI",
                "description": "Overview of artificial intelligence concepts",
                "keywords": ["AI", "machine learning", "introduction"],
                "confidence": 0.95
            }
        }


class ExtractionMetadataSchema(BaseModel):
    """Schema for timestamp extraction metadata."""
    total_topics: int
    extraction_method: str
    model_used: str


class TimestampResponse(BaseModel):
    """Response schema for timestamps."""
    timestamp_id: str
    file_id: str
    timestamps: List[TimestampEntrySchema]
    extraction_metadata: ExtractionMetadataSchema
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp_id": "ts-123e4567",
                "file_id": "file-123e4567",
                "timestamps": [
                    {
                        "timestamp_entry_id": "ts-entry-1",
                        "time": 0,
                        "topic": "Introduction",
                        "description": "Opening remarks",
                        "keywords": ["intro", "welcome"],
                        "confidence": 0.9
                    }
                ],
                "extraction_metadata": {
                    "total_topics": 5,
                    "extraction_method": "LLM-based",
                    "model_used": "gpt-4"
                },
                "created_at": "2026-01-29T10:00:00",
                "updated_at": "2026-01-29T10:00:00"
            }
        }
