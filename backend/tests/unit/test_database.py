"""
Unit tests for database module.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestConstants:
    """Test constants module."""

    def test_file_type_enum(self):
        """Test FileType enum values."""
        from app.core.constants import FileType

        assert FileType.PDF.value == "pdf"
        assert FileType.AUDIO.value == "audio"
        assert FileType.VIDEO.value == "video"

    def test_processing_status_enum(self):
        """Test ProcessingStatus enum values."""
        from app.core.constants import ProcessingStatus

        assert ProcessingStatus.PENDING.value == "pending"
        assert ProcessingStatus.PROCESSING.value == "processing"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"

    def test_message_role_enum(self):
        """Test MessageRole enum values."""
        from app.core.constants import MessageRole

        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"

    def test_summary_type_enum(self):
        """Test SummaryType enum values."""
        from app.core.constants import SummaryType

        assert SummaryType.BRIEF.value == "brief"
        assert SummaryType.DETAILED.value == "detailed"
        assert SummaryType.KEY_POINTS.value == "key_points"

    def test_collection_names(self):
        """Test collection name constants."""
        from app.core.constants import (
            COLLECTION_FILES,
            COLLECTION_SUMMARIES,
            COLLECTION_TIMESTAMPS,
            COLLECTION_CHAT_HISTORY
        )

        assert COLLECTION_FILES == "files"
        assert COLLECTION_SUMMARIES == "summaries"
        assert COLLECTION_TIMESTAMPS == "timestamps"
        assert COLLECTION_CHAT_HISTORY == "chat_history"

    def test_enums_are_string_enums(self):
        """Test that enums are string enums."""
        from app.core.constants import FileType, ProcessingStatus, MessageRole, SummaryType

        assert isinstance(FileType.PDF, str)
        assert isinstance(ProcessingStatus.PENDING, str)
        assert isinstance(MessageRole.USER, str)
        assert isinstance(SummaryType.BRIEF, str)


class TestDatabaseModule:
    """Test Database module."""

    def test_get_database_function_exists(self):
        """Test get_database function exists."""
        from app.core.database import get_database

        assert callable(get_database)

    def test_connect_function_exists(self):
        """Test connect_to_mongo function exists."""
        from app.core.database import connect_to_mongo

        assert callable(connect_to_mongo)

    def test_close_function_exists(self):
        """Test close_mongo_connection function exists."""
        from app.core.database import close_mongo_connection

        assert callable(close_mongo_connection)
