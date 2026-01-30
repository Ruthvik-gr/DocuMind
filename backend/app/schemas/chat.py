"""
Pydantic schemas for chat-related endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.core.constants import MessageRole


class ChatRequest(BaseModel):
    """Request schema for asking a question."""
    question: str = Field(..., min_length=1, max_length=1000)
    chat_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is this document about?",
                "chat_id": None
            }
        }


class ChatResponse(BaseModel):
    """Response schema for chat answer."""
    answer: str
    chat_id: str
    sources: List[str] = []
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "This document discusses AI-powered systems...",
                "chat_id": "chat-123e4567",
                "sources": ["chunk_1", "chunk_2"],
                "timestamp": "2026-01-29T10:00:00"
            }
        }


class MessageSchema(BaseModel):
    """Schema for a single chat message."""
    message_id: str
    role: MessageRole
    content: str
    timestamp: datetime
    token_count: Optional[int] = None
    metadata: Optional[dict] = None


class ChatHistoryResponse(BaseModel):
    """Response schema for chat history."""
    chat_id: str
    file_id: str
    messages: List[MessageSchema]
    total_messages: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "chat_id": "chat-123e4567",
                "file_id": "file-123e4567",
                "messages": [
                    {
                        "message_id": "msg-1",
                        "role": "user",
                        "content": "What is this about?",
                        "timestamp": "2026-01-29T10:00:00",
                        "token_count": 5
                    }
                ],
                "total_messages": 2,
                "total_tokens": 150,
                "created_at": "2026-01-29T10:00:00",
                "updated_at": "2026-01-29T10:05:00"
            }
        }
