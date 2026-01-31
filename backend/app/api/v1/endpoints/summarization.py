"""
Content summarization endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging

from app.services.file_service import file_service
from app.services.summary_service import summary_service
from app.schemas.summary import (
    SummaryRequest,
    SummaryResponse,
    SummaryListResponse,
    TokenCountSchema,
    SummaryParametersSchema
)
from app.core.constants import ProcessingStatus
from app.core.auth import get_current_user
from app.models.user import UserModel
from app.utils.exceptions import FileNotFoundError, ProcessingError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{file_id}/generate", response_model=SummaryResponse)
async def generate_summary(
    file_id: str,
    request: SummaryRequest,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Generate a summary for an uploaded file.

    The summary is generated using the file's extracted content and stored for future retrieval.
    """
    try:
        # Verify file exists and is processed
        file_model = await file_service.get_file(file_id, current_user.id)

        if file_model.processing_status != ProcessingStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"File is still being processed. Status: {file_model.processing_status.value}"
            )

        if not file_model.extracted_content:
            raise HTTPException(
                status_code=400,
                detail="No extracted content available for summarization"
            )

        # Generate summary
        summary_model = await summary_service.generate_summary(
            file_id=file_id,
            user_id=current_user.id,
            text=file_model.extracted_content.text,
            summary_type=request.summary_type
        )

        return SummaryResponse(
            summary_id=summary_model.summary_id,
            file_id=summary_model.file_id,
            summary_type=summary_model.summary_type,
            content=summary_model.content,
            model_used=summary_model.model_used,
            token_count=TokenCountSchema(
                input=summary_model.token_count.input,
                output=summary_model.token_count.output,
                total=summary_model.token_count.total
            ),
            parameters=SummaryParametersSchema(
                temperature=summary_model.parameters.temperature,
                max_tokens=summary_model.parameters.max_tokens
            ),
            created_at=summary_model.created_at
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
    except ProcessingError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Summarization failed for file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Summarization failed")


@router.get("/{file_id}", response_model=SummaryListResponse)
async def get_summaries(
    file_id: str,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all summaries for a file.
    """
    try:
        summaries = await summary_service.get_summaries(file_id, current_user.id)

        summary_responses = [
            SummaryResponse(
                summary_id=s.summary_id,
                file_id=s.file_id,
                summary_type=s.summary_type,
                content=s.content,
                model_used=s.model_used,
                token_count=TokenCountSchema(
                    input=s.token_count.input,
                    output=s.token_count.output,
                    total=s.token_count.total
                ),
                parameters=SummaryParametersSchema(
                    temperature=s.parameters.temperature,
                    max_tokens=s.parameters.max_tokens
                ),
                created_at=s.created_at
            )
            for s in summaries
        ]

        return SummaryListResponse(
            summaries=summary_responses,
            count=len(summary_responses)
        )

    except Exception as e:
        logger.error(f"Failed to get summaries for file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve summaries")
