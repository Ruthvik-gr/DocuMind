"""
File validation utilities.
"""
from fastapi import UploadFile
from app.config import get_settings
from app.core.constants import FileType
from app.utils.exceptions import InvalidFileError

settings = get_settings()


def validate_file_type(file: UploadFile) -> FileType:
    """
    Validate uploaded file type and return FileType enum.

    Args:
        file: Uploaded file object

    Returns:
        FileType enum value

    Raises:
        InvalidFileError: If file type is not allowed
    """
    mime_type = file.content_type

    if mime_type in settings.ALLOWED_PDF_MIMETYPES:
        return FileType.PDF
    elif mime_type in settings.ALLOWED_AUDIO_MIMETYPES:
        return FileType.AUDIO
    elif mime_type in settings.ALLOWED_VIDEO_MIMETYPES:
        return FileType.VIDEO
    else:
        raise InvalidFileError(
            f"File type '{mime_type}' is not allowed. "
            f"Allowed types: PDF, Audio (mp3, wav), Video (mp4, mov)"
        )


def validate_file_size(file: UploadFile) -> int:
    """
    Validate file size is within limits.

    Args:
        file: Uploaded file object

    Returns:
        File size in bytes

    Raises:
        InvalidFileError: If file is too large
    """
    # Read file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes

    if file_size > max_size:
        raise InvalidFileError(
            f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds "
            f"maximum allowed size ({settings.MAX_FILE_SIZE_MB} MB)"
        )

    return file_size
