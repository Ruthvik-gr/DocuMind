"""
Integration tests for chat endpoints.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime
import json


def parse_sse_events(content: str) -> list:
    """Parse SSE events from response content."""
    events = []
    for line in content.split('\n'):
        if line.startswith('data: '):
            try:
                data = json.loads(line[6:])
                events.append(data)
            except json.JSONDecodeError:
                pass
    return events


@pytest.mark.integration
class TestChatEndpoints:
    """Test chat-related endpoints."""

    def test_ask_question_file_not_found(self, test_client):
        """Test asking question on non-existent file."""
        from app.utils.exceptions import FileNotFoundError

        with patch('app.api.v1.endpoints.chat.file_service.get_file', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = FileNotFoundError("File not found")

            response = test_client.post(
                "/api/v1/chat/non-existent-id/ask",
                json={"question": "What is this about?"}
            )

            # Streaming endpoint always returns 200, error is in the stream
            assert response.status_code == 200
            events = parse_sse_events(response.text)
            assert len(events) > 0
            assert 'error' in events[-1]
            assert 'not found' in events[-1]['error'].lower()

    def test_ask_question_file_not_processed(self, test_client):
        """Test asking question when file is still processing."""
        from app.core.constants import ProcessingStatus

        with patch('app.api.v1.endpoints.chat.file_service.get_file', new_callable=AsyncMock) as mock_get:
            mock_file = MagicMock()
            mock_file.processing_status = ProcessingStatus.PROCESSING
            mock_get.return_value = mock_file

            response = test_client.post(
                "/api/v1/chat/test-id/ask",
                json={"question": "What is this about?"}
            )

            # Streaming endpoint returns 200, with error in stream
            assert response.status_code == 200
            events = parse_sse_events(response.text)
            assert len(events) > 0
            assert 'error' in events[-1]
            assert 'processing' in events[-1]['error'].lower()

    def test_ask_question_success(self, test_client, mock_db):
        """Test successful question answering."""
        from app.core.constants import ProcessingStatus

        async def mock_stream(*args, **kwargs):
            yield {"type": "content", "data": "This is "}
            yield {"type": "content", "data": "a test answer"}
            yield {"type": "sources", "data": ["chunk1", "chunk2"]}

        with patch('app.api.v1.endpoints.chat.file_service.get_file', new_callable=AsyncMock) as mock_file_get, \
             patch('app.api.v1.endpoints.chat.langchain_service.ask_question_stream') as mock_ask, \
             patch('app.api.v1.endpoints.chat.get_database') as mock_get_db:

            # Setup mock file
            mock_file = MagicMock()
            mock_file.processing_status = ProcessingStatus.COMPLETED
            mock_file.file_type = "pdf"
            mock_file_get.return_value = mock_file

            # Setup mock langchain streaming
            mock_ask.return_value = mock_stream()

            # Setup mock database
            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_collection.update_one = AsyncMock()
            mock_get_db.return_value = {"chat_history": mock_collection, "timestamps": mock_collection}

            response = test_client.post(
                "/api/v1/chat/test-id/ask",
                json={"question": "What is this about?"}
            )

            assert response.status_code == 200
            events = parse_sse_events(response.text)

            # Should have: start, content chunks, done
            assert len(events) >= 3
            assert events[0].get('type') == 'start'
            assert 'chat_id' in events[0]

            # Find content events
            content_events = [e for e in events if e.get('type') == 'content']
            assert len(content_events) >= 1

            # Find done event
            done_events = [e for e in events if e.get('type') == 'done']
            assert len(done_events) == 1

    def test_ask_question_with_existing_history(self, test_client, mock_db):
        """Test question with existing chat history."""
        from app.core.constants import ProcessingStatus, MessageRole

        async def mock_stream(*args, **kwargs):
            yield {"type": "content", "data": "Follow up answer"}
            yield {"type": "sources", "data": ["chunk1"]}

        with patch('app.api.v1.endpoints.chat.file_service.get_file', new_callable=AsyncMock) as mock_file_get, \
             patch('app.api.v1.endpoints.chat.langchain_service.ask_question_stream') as mock_ask, \
             patch('app.api.v1.endpoints.chat.get_database') as mock_get_db:

            mock_file = MagicMock()
            mock_file.processing_status = ProcessingStatus.COMPLETED
            mock_file.file_type = "pdf"
            mock_file_get.return_value = mock_file

            mock_ask.return_value = mock_stream()

            # Existing chat history
            existing_history = {
                "chat_id": "existing-chat",
                "user_id": "507f1f77bcf86cd799439011",
                "file_id": "test-id",
                "messages": [
                    {"message_id": "msg-1", "role": "user", "content": "First question", "timestamp": datetime.utcnow().isoformat(), "token_count": 2},
                    {"message_id": "msg-2", "role": "assistant", "content": "First answer", "timestamp": datetime.utcnow().isoformat(), "token_count": 2}
                ],
                "total_messages": 2,
                "total_tokens": 10,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value=existing_history)
            mock_collection.update_one = AsyncMock()
            mock_get_db.return_value = {"chat_history": mock_collection, "timestamps": mock_collection}

            response = test_client.post(
                "/api/v1/chat/test-id/ask",
                json={"question": "Follow up?", "chat_id": "existing-chat"}
            )

            assert response.status_code == 200
            events = parse_sse_events(response.text)
            assert len(events) >= 1

    def test_ask_question_processing_error(self, test_client):
        """Test processing error during Q&A."""
        from app.core.constants import ProcessingStatus
        from app.utils.exceptions import ProcessingError

        with patch('app.api.v1.endpoints.chat.file_service.get_file', new_callable=AsyncMock) as mock_file_get, \
             patch('app.api.v1.endpoints.chat.langchain_service.ask_question_stream') as mock_ask, \
             patch('app.api.v1.endpoints.chat.get_database') as mock_get_db:

            mock_file = MagicMock()
            mock_file.processing_status = ProcessingStatus.COMPLETED
            mock_file_get.return_value = mock_file

            mock_ask.side_effect = ProcessingError("LLM failed")

            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_get_db.return_value = {"chat_history": mock_collection}

            response = test_client.post(
                "/api/v1/chat/test-id/ask",
                json={"question": "What is this?"}
            )

            # Streaming endpoint returns 200, error is in stream
            assert response.status_code == 200
            events = parse_sse_events(response.text)
            # Error should be in the stream
            assert any('error' in e for e in events)

    def test_ask_question_generic_error(self, test_client):
        """Test generic error during Q&A."""
        from app.core.constants import ProcessingStatus

        with patch('app.api.v1.endpoints.chat.file_service.get_file', new_callable=AsyncMock) as mock_file_get, \
             patch('app.api.v1.endpoints.chat.get_database') as mock_get_db:

            mock_file = MagicMock()
            mock_file.processing_status = ProcessingStatus.COMPLETED
            mock_file_get.return_value = mock_file

            mock_get_db.side_effect = Exception("Database connection failed")

            response = test_client.post(
                "/api/v1/chat/test-id/ask",
                json={"question": "What is this?"}
            )

            # Streaming endpoint returns 200, error is in stream
            assert response.status_code == 200
            events = parse_sse_events(response.text)
            assert any('error' in e for e in events)

    def test_get_chat_history_empty(self, test_client):
        """Test getting empty chat history."""
        with patch('app.api.v1.endpoints.chat.get_database') as mock_get_db:
            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_get_db.return_value = {"chat_history": mock_collection}

            response = test_client.get("/api/v1/chat/test-id/history")

            assert response.status_code == 200
            data = response.json()
            assert data["messages"] == []
            assert data["total_messages"] == 0

    def test_get_chat_history_with_messages(self, test_client):
        """Test getting chat history with messages."""
        with patch('app.api.v1.endpoints.chat.get_database') as mock_get_db:
            history_doc = {
                "chat_id": "test-chat",
                "user_id": "507f1f77bcf86cd799439011",
                "file_id": "test-file",
                "messages": [
                    {
                        "message_id": "msg-1",
                        "role": "user",
                        "content": "Hello",
                        "timestamp": datetime.utcnow().isoformat(),
                        "token_count": 1
                    },
                    {
                        "message_id": "msg-2",
                        "role": "assistant",
                        "content": "Hi there!",
                        "timestamp": datetime.utcnow().isoformat(),
                        "token_count": 2,
                        "metadata": {
                            "source_chunks": ["chunk1"],
                            "model": "llama",
                            "confidence": 0.9
                        }
                    }
                ],
                "total_messages": 2,
                "total_tokens": 3,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value=history_doc)
            mock_get_db.return_value = {"chat_history": mock_collection}

            response = test_client.get("/api/v1/chat/test-file/history")

            assert response.status_code == 200
            data = response.json()
            assert len(data["messages"]) == 2
            assert data["total_messages"] == 2

    def test_get_chat_history_error(self, test_client):
        """Test error getting chat history."""
        with patch('app.api.v1.endpoints.chat.get_database') as mock_get_db:
            mock_get_db.side_effect = Exception("Database error")

            response = test_client.get("/api/v1/chat/test-id/history")

            assert response.status_code == 500
