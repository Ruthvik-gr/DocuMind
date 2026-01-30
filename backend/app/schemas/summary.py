"""
Pydantic schemas for summary-related endpoints.
"""
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from app.core.constants import SummaryType


class SummaryRequest(BaseModel):
    """Request schema for generating a summary."""
    summary_type: SummaryType = Field(default=SummaryType.BRIEF)

    class Config:
        json_schema_extra = {
            "example": {
                "summary_type": "brief"
            }
        }


class TokenCountSchema(BaseModel):
    """Schema for token count information."""
    input: int
    output: int
    total: int


class SummaryParametersSchema(BaseModel):
    """Schema for summary generation parameters."""
    temperature: float
    max_tokens: int


class SummaryResponse(BaseModel):
    """Response schema for summary."""
    summary_id: str
    file_id: str
    summary_type: SummaryType
    content: str
    model_used: str
    token_count: TokenCountSchema
    parameters: SummaryParametersSchema
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "summary_id": "sum-123e4567",
                "file_id": "file-123e4567",
                "summary_type": "brief",
                "content": "This document provides an overview of...",
                "model_used": "gpt-4",
                "token_count": {
                    "input": 1000,
                    "output": 150,
                    "total": 1150
                },
                "parameters": {
                    "temperature": 0.3,
                    "max_tokens": 500
                },
                "created_at": "2026-01-29T10:00:00"
            }
        }


class SummaryListResponse(BaseModel):
    """Response schema for list of summaries."""
    summaries: List[SummaryResponse]
    count: int
