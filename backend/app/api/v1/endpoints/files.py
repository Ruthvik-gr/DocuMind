"""
File management endpoints.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from app.services.file_service import file_service
from app.services.pdf_service import pdf_service
from app.services.transcription_service import transcription_service
from app.services.langchain_service import langchain_service
from app.services.cloudinary_service import cloudinary_service
from app.schemas.file import FileUploadResponse, FileDetailResponse, FileListItem, FileListResponse
from app.core.constants import FileType, ProcessingStatus, COLLECTION_CHAT_HISTORY, COLLECTION_USERS
from app.core.database import get_database
from app.core.auth import get_current_user, decode_token
from app.models.user import UserModel
from app.utils.exceptions import (
    InvalidFileError,
    FileNotFoundError,
    ProcessingError
)

security = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)
router = APIRouter()


async def process_file_background(file_id: str, cloudinary_url: str, file_type: FileType, filename: str):
    """Background task to process uploaded file from Cloudinary."""
    temp_file_path = None
    try:
        await file_service.update_processing_status(file_id, ProcessingStatus.PROCESSING)

        # Download file from Cloudinary to temp location for processing
        file_extension = {
            FileType.PDF: '.pdf',
            FileType.VIDEO: '.mp4',
            FileType.AUDIO: '.mp3'
        }.get(file_type, '')

        temp_file_path = await cloudinary_service.download_to_temp(
            cloudinary_url=cloudinary_url,
            suffix=file_extension
        )
        logger.info(f"Downloaded file from Cloudinary to temp: {temp_file_path}")

        if file_type == FileType.PDF:
            # Extract text from PDF
            extracted_content = pdf_service.extract_text(temp_file_path)
            await file_service.update_extracted_content(file_id, extracted_content)

            # Create vector store for Q&A
            await langchain_service.create_vector_store(
                file_id=file_id,
                text=extracted_content.text,
                metadata={"file_id": file_id, "file_type": "pdf"}
            )

        elif file_type in [FileType.AUDIO, FileType.VIDEO]:
            # Transcribe audio/video
            extracted_content, metadata = await transcription_service.transcribe_file(temp_file_path)
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
    finally:
        # Clean up temporary file
        if temp_file_path:
            try:
                import os
                os.unlink(temp_file_path)
                logger.info(f"Deleted temp file: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete temp file: {cleanup_error}")


@router.get("/", response_model=FileListResponse)
async def list_files(current_user: UserModel = Depends(get_current_user)):
    """
    List all files for the current user.
    """
    try:
        files = await file_service.list_files(current_user.id)
        db = get_database()

        # Check which files have chat history
        file_items = []
        for file_model in files:
            chat_exists = await db[COLLECTION_CHAT_HISTORY].find_one(
                {"file_id": file_model.file_id, "user_id": current_user.id}
            )
            file_items.append(FileListItem(
                file_id=file_model.file_id,
                filename=file_model.filename,
                file_type=file_model.file_type,
                file_size=file_model.file_size,
                processing_status=file_model.processing_status,
                created_at=file_model.created_at,
                has_chat=chat_exists is not None
            ))

        return FileListResponse(
            files=file_items,
            total=len(file_items)
        )

    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        raise HTTPException(status_code=500, detail="Failed to list files")


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Upload a PDF, audio, or video file to Cloudinary.

    The file will be processed in the background to extract content.
    """
    try:
        # Upload file to Cloudinary (no local storage)
        file_model = await file_service.upload_file(file, current_user.id)

        # Add background task for processing
        background_tasks.add_task(
            process_file_background,
            file_model.file_id,
            file_model.cloudinary_url,
            file_model.file_type,
            file_model.filename
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
async def stream_file(
    file_id: str,
    token: Optional[str] = Query(None, description="JWT token for authentication"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Stream a file for media playback.
    Accepts authentication via Bearer token header OR token query parameter.
    Redirects to Cloudinary URL if available, otherwise serves from local storage.
    """
    # Get token from either query param or header
    auth_token = token
    if not auth_token and credentials:
        auth_token = credentials.credentials

    if not auth_token:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Decode and validate token
    payload = decode_token(auth_token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        file_model = await file_service.get_file(file_id, user_id)

        # Files are stored in Cloudinary only
        if not file_model.cloudinary_url:
            raise HTTPException(
                status_code=404,
                detail="File not available for streaming. Processing may not be complete."
            )

        return RedirectResponse(url=file_model.cloudinary_url)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to stream file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stream file")


@router.delete("/{file_id}")
async def delete_file(file_id: str, current_user: UserModel = Depends(get_current_user)):
    """
    Delete a file.
    """
    try:
        await file_service.delete_file(file_id, current_user.id)
        return {"message": "File deleted successfully"}

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
    except Exception as e:
        logger.error(f"Failed to delete file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete file")
