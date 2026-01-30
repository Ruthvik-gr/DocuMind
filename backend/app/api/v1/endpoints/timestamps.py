"""
Timestamp extraction endpoints.
"""
from fastapi import APIRouter, HTTPException
import logging

from app.services.file_service import file_service
from app.services.timestamp_service import timestamp_service
from app.schemas.timestamp import (
    TimestampResponse,
    TimestampEntrySchema,
    ExtractionMetadataSchema
)
from app.core.constants import FileType, ProcessingStatus
from app.utils.exceptions import FileNotFoundError, ProcessingError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{file_id}/extract", response_model=TimestampResponse)
async def extract_timestamps(file_id: str):
    """
    Extract timestamps and topics from an audio/video file.

    This endpoint analyzes the transcription to identify major topics and their timestamps.
    """
    try:
        # Verify file exists and is processed
        file_model = await file_service.get_file(file_id)

        if file_model.processing_status != ProcessingStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"File is still being processed. Status: {file_model.processing_status.value}"
            )

        if file_model.file_type not in [FileType.AUDIO, FileType.VIDEO]:
            raise HTTPException(
                status_code=400,
                detail="Timestamp extraction is only available for audio/video files"
            )

        if not file_model.extracted_content:
            raise HTTPException(
                status_code=400,
                detail="No transcription available for timestamp extraction"
            )

        # Get duration from metadata
        duration = file_model.metadata.duration if file_model.metadata else 0

        # Extract timestamps
        timestamp_model = await timestamp_service.extract_timestamps(
            file_id=file_id,
            transcription=file_model.extracted_content.text,
            duration=duration
        )

        # Convert to response schema
        timestamp_entries = [
            TimestampEntrySchema(
                timestamp_entry_id=entry.timestamp_entry_id,
                time=entry.time,
                topic=entry.topic,
                description=entry.description,
                keywords=entry.keywords,
                confidence=entry.confidence
            )
            for entry in timestamp_model.timestamps
        ]

        return TimestampResponse(
            timestamp_id=timestamp_model.timestamp_id,
            file_id=timestamp_model.file_id,
            timestamps=timestamp_entries,
            extraction_metadata=ExtractionMetadataSchema(
                total_topics=timestamp_model.extraction_metadata.total_topics,
                extraction_method=timestamp_model.extraction_metadata.extraction_method,
                model_used=timestamp_model.extraction_metadata.model_used
            ),
            created_at=timestamp_model.created_at,
            updated_at=timestamp_model.updated_at
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
    except ProcessingError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Timestamp extraction failed for file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Timestamp extraction failed")


@router.get("/{file_id}", response_model=TimestampResponse)
async def get_timestamps(file_id: str):
    """
    Get extracted timestamps for a file.
    """
    try:
        timestamp_model = await timestamp_service.get_timestamps(file_id)

        if not timestamp_model:
            raise HTTPException(
                status_code=404,
                detail="No timestamps found for this file. Use POST /timestamps/{file_id}/extract to generate them."
            )

        # Convert to response schema
        timestamp_entries = [
            TimestampEntrySchema(
                timestamp_entry_id=entry.timestamp_entry_id,
                time=entry.time,
                topic=entry.topic,
                description=entry.description,
                keywords=entry.keywords,
                confidence=entry.confidence
            )
            for entry in timestamp_model.timestamps
        ]

        return TimestampResponse(
            timestamp_id=timestamp_model.timestamp_id,
            file_id=timestamp_model.file_id,
            timestamps=timestamp_entries,
            extraction_metadata=ExtractionMetadataSchema(
                total_topics=timestamp_model.extraction_metadata.total_topics,
                extraction_method=timestamp_model.extraction_metadata.extraction_method,
                model_used=timestamp_model.extraction_metadata.model_used
            ),
            created_at=timestamp_model.created_at,
            updated_at=timestamp_model.updated_at
        )

    except Exception as e:
        logger.error(f"Failed to get timestamps for file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve timestamps")
