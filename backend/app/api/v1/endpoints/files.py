"""
File management endpoints.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from typing import List
import logging
import os

from app.services.file_service import file_service
from app.services.pdf_service import pdf_service
from app.services.transcription_service import transcription_service
from app.services.langchain_service import langchain_service
from app.schemas.file import FileUploadResponse, FileDetailResponse
from app.core.constants import FileType, ProcessingStatus
from app.core.auth import get_current_user
from app.models.user import UserModel
from app.utils.exceptions import (
    InvalidFileError,
    FileNotFoundError,
    ProcessingError
)

logger = logging.getLogger(__name__)
router = APIRouter()


async def process_file_background(file_id: str, file_path: str, file_type: FileType):
    """Background task to process uploaded file."""
    try:
        await file_service.update_processing_status(file_id, ProcessingStatus.PROCESSING)

        if file_type == FileType.PDF:
            # Extract text from PDF
            extracted_content = pdf_service.extract_text(file_path)
            await file_service.update_extracted_content(file_id, extracted_content)

            # Create vector store for Q&A
            await langchain_service.create_vector_store(
                file_id=file_id,
                text=extracted_content.text,
                metadata={"file_id": file_id, "file_type": "pdf"}
            )

        elif file_type in [FileType.AUDIO, FileType.VIDEO]:
            # Transcribe audio/video
            extracted_content, metadata = await transcription_service.transcribe_file(file_path)
            await file_service.update_extracted_content(file_id, extracted_content)
            await file_service.update_metadata(file_id, metadata)

            # Create vector store for Q&A
            await langchain_service.create_vector_store(
                file_id=file_id,
                text=extracted_content.text,
                metadata={"file_id": file_id, "file_type": file_type.value}
            )

        await file_service.update_processing_status(file_id, ProcessingStatus.COMPLETED)
        logger.info(f"Successfully processed file {file_id}")

    except Exception as e:
        logger.error(f"Failed to process file {file_id}: {e}")
        await file_service.update_processing_status(
            file_id,
            ProcessingStatus.FAILED,
            error=str(e)
        )


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Upload a PDF, audio, or video file.

    The file will be processed in the background to extract content.
    """
    try:
        # Upload and save file
        file_model = await file_service.upload_file(file, current_user.id)

        # Add background task for processing
        background_tasks.add_task(
            process_file_background,
            file_model.file_id,
            file_model.file_path,
            file_model.file_type
        )

        return FileUploadResponse(
            file_id=file_model.file_id,
            filename=file_model.filename,
            file_type=file_model.file_type,
            file_size=file_model.file_size,
            processing_status=file_model.processing_status,
            upload_date=file_model.upload_date
        )

    except InvalidFileError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")


@router.get("/{file_id}", response_model=FileDetailResponse)
async def get_file(file_id: str, current_user: UserModel = Depends(get_current_user)):
    """
    Get file details including extracted content.
    """
    try:
        file_model = await file_service.get_file(file_id, current_user.id)

        # Convert nested models to dicts for schema compatibility
        extracted_content_dict = None
        if file_model.extracted_content:
            extracted_content_dict = file_model.extracted_content.model_dump()

        metadata_dict = None
        if file_model.metadata:
            metadata_dict = file_model.metadata.model_dump()

        return FileDetailResponse(
            file_id=file_model.file_id,
            filename=file_model.filename,
            file_type=file_model.file_type,
            file_size=file_model.file_size,
            mime_type=file_model.mime_type,
            processing_status=file_model.processing_status,
            processing_error=file_model.processing_error,
            extracted_content=extracted_content_dict,
            metadata=metadata_dict,
            upload_date=file_model.upload_date,
            created_at=file_model.created_at,
            updated_at=file_model.updated_at
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
    except Exception as e:
        logger.error(f"Failed to get file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file")


@router.get("/{file_id}/stream")
async def stream_file(file_id: str, current_user: UserModel = Depends(get_current_user)):
    """
    Stream a file for media playback.
    """
    try:
        file_model = await file_service.get_file(file_id, current_user.id)

        if not os.path.exists(file_model.file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")

        return FileResponse(
            path=file_model.file_path,
            filename=file_model.filename,
            media_type=file_model.mime_type
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
    except Exception as e:
        logger.error(f"Failed to stream file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stream file")
