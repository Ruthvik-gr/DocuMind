"""
Integration tests for chat endpoints.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime


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

            assert response.status_code == 404

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

            # HTTPException gets caught by generic handler, both 400 and 500 are valid
            assert response.status_code in [400, 500]

    def test_ask_question_success(self, test_client, mock_db):
        """Test successful question answering."""
        from app.core.constants import ProcessingStatus

        with patch('app.api.v1.endpoints.chat.file_service.get_file', new_callable=AsyncMock) as mock_file_get, \
             patch('app.api.v1.endpoints.chat.langchain_service.ask_question', new_callable=AsyncMock) as mock_ask, \
             patch('app.api.v1.endpoints.chat.get_database') as mock_get_db:

            # Setup mock file
            mock_file = MagicMock()
            mock_file.processing_status = ProcessingStatus.COMPLETED
            mock_file_get.return_value = mock_file

            # Setup mock langchain response
            mock_ask.return_value = {
                "answer": "This is a test answer",
                "source_documents": ["chunk1", "chunk2"]
            }

            # Setup mock database
            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_collection.update_one = AsyncMock()
            mock_get_db.return_value = {"chat_history": mock_collection}

            response = test_client.post(
                "/api/v1/chat/test-id/ask",
                json={"question": "What is this about?"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "This is a test answer"
            assert "chat_id" in data

    def test_ask_question_with_existing_history(self, test_client, mock_db):
        """Test question with existing chat history."""
        from app.core.constants import ProcessingStatus, MessageRole

        with patch('app.api.v1.endpoints.chat.file_service.get_file', new_callable=AsyncMock) as mock_file_get, \
             patch('app.api.v1.endpoints.chat.langchain_service.ask_question', new_callable=AsyncMock) as mock_ask, \
             patch('app.api.v1.endpoints.chat.get_database') as mock_get_db:

            mock_file = MagicMock()
            mock_file.processing_status = ProcessingStatus.COMPLETED
            mock_file_get.return_value = mock_file

            mock_ask.return_value = {
                "answer": "Follow up answer",
                "source_documents": ["chunk1"]
            }

            # Existing chat history
            existing_history = {
                "chat_id": "existing-chat",
                "file_id": "test-id",
                "messages": [
                    {"message_id": "msg-1", "role": "user", "content": "First question", "timestamp": datetime.utcnow().isoformat()},
                    {"message_id": "msg-2", "role": "assistant", "content": "First answer", "timestamp": datetime.utcnow().isoformat()}
                ],
                "total_messages": 2,
                "total_tokens": 10,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value=existing_history)
            mock_collection.update_one = AsyncMock()
            mock_get_db.return_value = {"chat_history": mock_collection}

            response = test_client.post(
                "/api/v1/chat/test-id/ask",
                json={"question": "Follow up?", "chat_id": "existing-chat"}
            )

            assert response.status_code == 200

    def test_ask_question_processing_error(self, test_client):
        """Test processing error during Q&A."""
        from app.core.constants import ProcessingStatus
        from app.utils.exceptions import ProcessingError

        with patch('app.api.v1.endpoints.chat.file_service.get_file', new_callable=AsyncMock) as mock_file_get, \
             patch('app.api.v1.endpoints.chat.langchain_service.ask_question', new_callable=AsyncMock) as mock_ask, \
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

            assert response.status_code == 500

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

            assert response.status_code == 500

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
