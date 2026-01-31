"""
Pytest configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import io
import os

from app.main import app
from app.core.database import get_database


@pytest.fixture
def mock_db():
    """Mock database that returns AsyncMock for all collection operations."""
    mock = MagicMock()

    # Mock collection operations
    mock_collection = AsyncMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="test_id"))
    mock_collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    mock_collection.find = MagicMock(return_value=AsyncMock())

    # Return mock collection for any collection access
    mock.__getitem__ = MagicMock(return_value=mock_collection)

    return mock


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    from app.models.user import UserModel
    return UserModel(
        id="507f1f77bcf86cd799439011",
        email="test@example.com",
        name="Test User",
        auth_provider="local",
        password_hash="hashed_password"
    )


@pytest.fixture
def test_client(mock_db, mock_user):
    """FastAPI test client with mocked database and authentication."""
    from app.core.auth import get_current_user

    async def mock_get_current_user():
        return mock_user

    with patch('app.main.connect_to_mongo', new_callable=AsyncMock) as mock_connect, \
         patch('app.main.close_mongo_connection', new_callable=AsyncMock) as mock_close:

        app.dependency_overrides[get_database] = lambda: mock_db
        app.dependency_overrides[get_current_user] = mock_get_current_user

        with TestClient(app) as client:
            yield client

        app.dependency_overrides.clear()


@pytest.fixture
def sample_pdf_file():
    """Sample PDF file for testing."""
    pdf_content = b"%PDF-1.4\n%Test PDF Content"
    return ("test.pdf", io.BytesIO(pdf_content), "application/pdf")


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return "This is a sample text for testing purposes. It contains multiple sentences."


@pytest.fixture
def mock_groq_response(monkeypatch):
    """Mock Groq API responses."""
    class MockChoice:
        def __init__(self, text="Mocked response"):
            self.message = MagicMock()
            self.message.content = text

    class MockResponse:
        def __init__(self, text="Mocked response"):
            self.choices = [MockChoice(text)]
            self.usage = MagicMock()
            self.usage.prompt_tokens = 100
            self.usage.completion_tokens = 50
            self.usage.total_tokens = 150

    class MockCompletions:
        async def create(self, *args, **kwargs):
            return MockResponse()

    class MockChat:
        def __init__(self):
            self.completions = MockCompletions()

    class MockGroqClient:
        def __init__(self, *args, **kwargs):
            self.chat = MockChat()

    monkeypatch.setattr("groq.AsyncGroq", MockGroqClient)


@pytest.fixture
def mock_whisper(monkeypatch):
    """Mock Whisper transcription."""
    class MockSegment:
        def __init__(self):
            self.start = 0.0
            self.end = 10.0
            self.text = "Sample transcription text"

    class MockTranscriptionInfo:
        def __init__(self):
            self.language = "en"
            self.duration = 120.0

    class MockWhisperModel:
        def __init__(self, *args, **kwargs):
            pass

        def transcribe(self, *args, **kwargs):
            segments = [MockSegment()]
            info = MockTranscriptionInfo()
            return segments, info

    monkeypatch.setattr("faster_whisper.WhisperModel", MockWhisperModel)


@pytest.fixture
def mock_cloudinary(monkeypatch):
    """Mock Cloudinary service."""
    def mock_upload(*args, **kwargs):
        return {
            "secure_url": "https://cloudinary.com/test/video.mp4",
            "public_id": "documind/videos/test-id",
            "resource_type": "video"
        }

    def mock_destroy(*args, **kwargs):
        return {"result": "ok"}

    monkeypatch.setattr("cloudinary.uploader.upload", mock_upload)
    monkeypatch.setattr("cloudinary.uploader.destroy", mock_destroy)


@pytest.fixture
def mock_auth_token():
    """Mock authentication for tests."""
    return "test-jwt-token"
