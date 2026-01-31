"""
Database model for summaries collection.
"""
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.core.constants import SummaryType


class TokenCount(BaseModel):
    """Token count subdocument."""
    input: int
    output: int
    total: int


class SummaryParameters(BaseModel):
    """Summary generation parameters subdocument."""
    temperature: float
    max_tokens: int


class SummaryModel(BaseModel):
    """Summary document model."""
    summary_id: str
    user_id: str
    file_id: str
    summary_type: SummaryType
    content: str
    model_used: str
    token_count: TokenCount
    parameters: SummaryParameters
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for MongoDB insertion."""
        data = self.model_dump()
        data['summary_type'] = self.summary_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SummaryModel":
        """Create model from MongoDB document."""
        if '_id' in data:
            del data['_id']
        return cls(**data)
