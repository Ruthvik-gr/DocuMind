"""
Database model for chat_history collection.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.core.constants import MessageRole


class MessageMetadata(BaseModel):
    """Message metadata subdocument."""
    source_chunks: List[str] = []
    model: Optional[str] = None
    confidence: Optional[float] = None


class Message(BaseModel):
    """Individual message subdocument."""
    message_id: str
    role: MessageRole
    content: str
    timestamp: datetime
    token_count: Optional[int] = None
    metadata: Optional[MessageMetadata] = None


class ChatHistoryModel(BaseModel):
    """Chat history document model."""
    chat_id: str
    user_id: str
    file_id: str
    messages: List[Message] = []
    total_messages: int = 0
    total_tokens: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for MongoDB insertion."""
        data = self.model_dump()
        # Convert message roles to strings
        for msg in data['messages']:
            msg['role'] = msg['role'] if isinstance(msg['role'], str) else msg['role'].value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatHistoryModel":
        """Create model from MongoDB document."""
        if '_id' in data:
            del data['_id']
        return cls(**data)
