"""
Unit tests for data models.
"""
import pytest
from datetime import datetime

from app.models.file import FileModel, ExtractedContent, FileMetadata
from app.models.chat import ChatHistoryModel, Message, MessageMetadata
from app.models.summary import SummaryModel, TokenCount, SummaryParameters
from app.models.timestamp import TimestampModel, TimestampEntry, ExtractionMetadata
from app.core.constants import FileType, ProcessingStatus, MessageRole, SummaryType


class TestFileModels:
    """Test file-related models."""

    def test_extracted_content_model(self):
        """Test ExtractedContent model."""
        content = ExtractedContent(
            text="Sample text",
            word_count=2,
            language="en",
            extraction_method="PyPDF2"
        )

        assert content.text == "Sample text"
        assert content.word_count == 2

        data = content.model_dump()
        assert data["text"] == "Sample text"

    def test_file_metadata_model(self):
        """Test FileMetadata model."""
        metadata = FileMetadata(
            duration=120,
            format="mp3",
            resolution=None,
            sample_rate=44100,
            channels=2
        )

        assert metadata.duration == 120
        assert metadata.format == "mp3"
        assert metadata.sample_rate == 44100

    def test_file_model_creation(self):
        """Test FileModel creation."""
        file = FileModel(
            file_id="test-id",
            user_id="user-123",
            filename="test.pdf",
            file_type=FileType.PDF,
            file_path="/path/to/file",
            file_size=1024,
            mime_type="application/pdf",
            upload_date=datetime.utcnow(),
            processing_status=ProcessingStatus.PENDING
        )

        assert file.file_id == "test-id"
        assert file.user_id == "user-123"
        assert file.file_type == FileType.PDF
        assert file.processing_status == ProcessingStatus.PENDING

    def test_file_model_to_dict(self):
        """Test FileModel to_dict method."""
        file = FileModel(
            file_id="test-id",
            user_id="user-123",
            filename="test.pdf",
            file_type=FileType.PDF,
            file_path="/path/to/file",
            file_size=1024,
            mime_type="application/pdf",
            upload_date=datetime.utcnow(),
            processing_status=ProcessingStatus.COMPLETED,
            extracted_content=ExtractedContent(
                text="content",
                word_count=1,
                language="en",
                extraction_method="PyPDF2"
            )
        )

        data = file.to_dict()

        assert data["file_id"] == "test-id"
        assert data["user_id"] == "user-123"
        assert data["file_type"] == "pdf"
        assert data["processing_status"] == "completed"
        assert "extracted_content" in data

    def test_file_model_from_dict(self):
        """Test FileModel from_dict method."""
        data = {
            "file_id": "test-id",
            "user_id": "user-123",
            "filename": "test.pdf",
            "file_type": "pdf",
            "file_path": "/path/to/file",
            "file_size": 1024,
            "mime_type": "application/pdf",
            "upload_date": datetime.utcnow().isoformat(),
            "processing_status": "completed",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "extracted_content": {
                "text": "content",
                "word_count": 1,
                "language": "en",
                "extraction_method": "PyPDF2"
            }
        }

        file = FileModel.from_dict(data)

        assert file.file_id == "test-id"
        assert file.user_id == "user-123"
        assert file.file_type == FileType.PDF
        assert file.extracted_content.text == "content"


class TestChatModels:
    """Test chat-related models."""

    def test_message_metadata_model(self):
        """Test MessageMetadata model."""
        metadata = MessageMetadata(
            source_chunks=["chunk1", "chunk2"],
            model="llama-3.3",
            confidence=0.95
        )

        assert len(metadata.source_chunks) == 2
        assert metadata.model == "llama-3.3"
        assert metadata.confidence == 0.95

    def test_message_model(self):
        """Test Message model."""
        message = Message(
            message_id="msg-1",
            role=MessageRole.USER,
            content="Hello",
            timestamp=datetime.utcnow(),
            token_count=1
        )

        assert message.message_id == "msg-1"
        assert message.role == MessageRole.USER
        assert message.content == "Hello"

    def test_chat_history_model_to_dict(self):
        """Test ChatHistoryModel to_dict method."""
        chat = ChatHistoryModel(
            chat_id="chat-1",
            user_id="user-123",
            file_id="file-1",
            messages=[
                Message(
                    message_id="msg-1",
                    role=MessageRole.USER,
                    content="Hi",
                    timestamp=datetime.utcnow(),
                    token_count=1
                )
            ],
            total_messages=1,
            total_tokens=1
        )

        data = chat.to_dict()

        assert data["chat_id"] == "chat-1"
        assert data["user_id"] == "user-123"
        assert len(data["messages"]) == 1
        assert data["messages"][0]["role"] == "user"

    def test_chat_history_model_from_dict(self):
        """Test ChatHistoryModel from_dict method."""
        data = {
            "chat_id": "chat-1",
            "user_id": "user-123",
            "file_id": "file-1",
            "messages": [
                {
                    "message_id": "msg-1",
                    "role": "assistant",
                    "content": "Hello!",
                    "timestamp": datetime.utcnow().isoformat(),
                    "token_count": 1,
                    "metadata": {
                        "source_chunks": ["chunk1"],
                        "model": "llama",
                        "confidence": 0.9
                    }
                }
            ],
            "total_messages": 1,
            "total_tokens": 1,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        chat = ChatHistoryModel.from_dict(data)

        assert chat.chat_id == "chat-1"
        assert chat.user_id == "user-123"
        assert len(chat.messages) == 1
        assert chat.messages[0].role == MessageRole.ASSISTANT
        assert chat.messages[0].metadata.model == "llama"


class TestSummaryModels:
    """Test summary-related models."""

    def test_token_count_model(self):
        """Test TokenCount model."""
        count = TokenCount(input=100, output=50, total=150)

        assert count.input == 100
        assert count.output == 50
        assert count.total == 150

    def test_summary_parameters_model(self):
        """Test SummaryParameters model."""
        params = SummaryParameters(temperature=0.3, max_tokens=500)

        assert params.temperature == 0.3
        assert params.max_tokens == 500

    def test_summary_model_to_dict(self):
        """Test SummaryModel to_dict method."""
        summary = SummaryModel(
            summary_id="sum-1",
            user_id="user-123",
            file_id="file-1",
            summary_type=SummaryType.BRIEF,
            content="Brief summary",
            model_used="llama-3.3",
            token_count=TokenCount(input=100, output=50, total=150),
            parameters=SummaryParameters(temperature=0.3, max_tokens=500)
        )

        data = summary.to_dict()

        assert data["summary_id"] == "sum-1"
        assert data["user_id"] == "user-123"
        assert data["summary_type"] == "brief"
        assert data["token_count"]["total"] == 150

    def test_summary_model_from_dict(self):
        """Test SummaryModel from_dict method."""
        data = {
            "summary_id": "sum-1",
            "user_id": "user-123",
            "file_id": "file-1",
            "summary_type": "detailed",
            "content": "Detailed summary",
            "model_used": "llama",
            "token_count": {"input": 100, "output": 50, "total": 150},
            "parameters": {"temperature": 0.3, "max_tokens": 500},
            "created_at": datetime.utcnow().isoformat()
        }

        summary = SummaryModel.from_dict(data)

        assert summary.summary_id == "sum-1"
        assert summary.user_id == "user-123"
        assert summary.summary_type == SummaryType.DETAILED
        assert summary.content == "Detailed summary"


class TestTimestampModels:
    """Test timestamp-related models."""

    def test_timestamp_entry_model(self):
        """Test TimestampEntry model."""
        entry = TimestampEntry(
            timestamp_entry_id="entry-1",
            time=60,
            topic="Introduction",
            description="Overview",
            keywords=["intro", "overview"],
            confidence=0.95
        )

        assert entry.time == 60
        assert entry.topic == "Introduction"
        assert len(entry.keywords) == 2

    def test_extraction_metadata_model(self):
        """Test ExtractionMetadata model."""
        metadata = ExtractionMetadata(
            total_topics=5,
            extraction_method="llm",
            model_used="llama"
        )

        assert metadata.total_topics == 5
        assert metadata.extraction_method == "llm"

    def test_timestamp_model_to_dict(self):
        """Test TimestampModel to_dict method."""
        timestamp = TimestampModel(
            timestamp_id="ts-1",
            user_id="user-123",
            file_id="file-1",
            timestamps=[
                TimestampEntry(
                    timestamp_entry_id="entry-1",
                    time=0,
                    topic="Intro",
                    description="Start",
                    keywords=["intro"],
                    confidence=0.9
                )
            ],
            extraction_metadata=ExtractionMetadata(
                total_topics=1,
                extraction_method="llm",
                model_used="llama"
            )
        )

        data = timestamp.to_dict()

        assert data["timestamp_id"] == "ts-1"
        assert data["user_id"] == "user-123"
        assert len(data["timestamps"]) == 1
        assert data["extraction_metadata"]["total_topics"] == 1

    def test_timestamp_model_from_dict(self):
        """Test TimestampModel from_dict method."""
        data = {
            "timestamp_id": "ts-1",
            "user_id": "user-123",
            "file_id": "file-1",
            "timestamps": [
                {
                    "timestamp_entry_id": "entry-1",
                    "time": 60,
                    "topic": "Topic",
                    "description": "Desc",
                    "keywords": ["key"],
                    "confidence": 0.8
                }
            ],
            "extraction_metadata": {
                "total_topics": 1,
                "extraction_method": "llm",
                "model_used": "llama"
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        timestamp = TimestampModel.from_dict(data)

        assert timestamp.timestamp_id == "ts-1"
        assert len(timestamp.timestamps) == 1
        assert timestamp.timestamps[0].time == 60
