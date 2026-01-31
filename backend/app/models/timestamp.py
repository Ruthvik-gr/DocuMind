"""
Database model for timestamps collection.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TimestampEntry(BaseModel):
    """Individual timestamp entry subdocument."""
    timestamp_entry_id: str
    time: int  # Time in seconds
    topic: str
    description: str
    keywords: List[str] = []
    confidence: Optional[float] = None


class ExtractionMetadata(BaseModel):
    """Timestamp extraction metadata subdocument."""
    total_topics: int
    extraction_method: str
    model_used: str


class TimestampModel(BaseModel):
    """Timestamp document model."""
    timestamp_id: str
    user_id: str
    file_id: str
    timestamps: List[TimestampEntry]
    extraction_metadata: ExtractionMetadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for MongoDB insertion."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimestampModel":
        """Create model from MongoDB document."""
        if '_id' in data:
            del data['_id']
        return cls(**data)
