"""
Custom exceptions for the application.
"""


class DocuMindException(Exception):
    """Base exception for DocuMind application."""
    pass


class InvalidFileError(DocuMindException):
    """Raised when file is invalid or corrupted."""
    pass


class FileNotFoundError(DocuMindException):
    """Raised when file is not found."""
    pass


class ProcessingError(DocuMindException):
    """Raised when file processing fails."""
    pass


class DatabaseError(DocuMindException):
    """Raised when database operation fails."""
    pass


class ExternalAPIError(DocuMindException):
    """Raised when external API call fails."""
    pass
