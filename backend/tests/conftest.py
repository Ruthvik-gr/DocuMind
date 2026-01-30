"""
Pytest configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient
from unittest.mock import AsyncMock, patch, MagicMock
import io

from app.main import app
from app.core.database import get_database


@pytest.fixture
def mock_db():
    """Mock MongoDB for testing."""
    client = AsyncMongoMockClient()
    db = client.test_database
    return db


@pytest.fixture
def test_client(mock_db):
    """FastAPI test client with mocked database."""
    # Mock the database connection functions where they're imported in main.py
    with patch('app.main.connect_to_mongo', new_callable=AsyncMock) as mock_connect, \
         patch('app.main.close_mongo_connection', new_callable=AsyncMock) as mock_close:

        app.dependency_overrides[get_database] = lambda: mock_db

        with TestClient(app) as client:
            yield client

        app.dependency_overrides.clear()


@pytest.fixture
def sample_pdf_file():
    """Sample PDF file for testing."""
    # Create a simple PDF-like content
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
