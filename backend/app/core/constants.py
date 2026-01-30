"""
Application constants.
"""
from enum import Enum


class FileType(str, Enum):
    """File type enumeration."""
    PDF = "pdf"
    AUDIO = "audio"
    VIDEO = "video"


class ProcessingStatus(str, Enum):
    """Processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageRole(str, Enum):
    """Chat message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"


class SummaryType(str, Enum):
    """Summary type enumeration."""
    BRIEF = "brief"
    DETAILED = "detailed"
    KEY_POINTS = "key_points"


# Collection names
COLLECTION_FILES = "files"
COLLECTION_SUMMARIES = "summaries"
COLLECTION_TIMESTAMPS = "timestamps"
COLLECTION_CHAT_HISTORY = "chat_history"
