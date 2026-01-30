"""
Pytest configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient
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
def mock_openai_response(monkeypatch):
    """Mock OpenAI API responses."""
    class MockResponse:
        def __init__(self, text="Mocked response", usage=None):
            self.text = text
            self.content = text
            self.choices = [type('obj', (object,), {
                'message': type('obj', (object,), {'content': text})()
            })()]
            self.usage = usage or type('obj', (object,), {
                'prompt_tokens': 100,
                'completion_tokens': 50,
                'total_tokens': 150
            })()

    async def mock_create(*args, **kwargs):
        return MockResponse()

    async def mock_atranscribe(*args, **kwargs):
        return {
            "text": "Sample transcription",
            "duration": 120,
            "language": "en"
        }

    monkeypatch.setattr("openai.ChatCompletion.acreate", mock_create)
    monkeypatch.setattr("openai.Audio.atranscribe", mock_atranscribe)
