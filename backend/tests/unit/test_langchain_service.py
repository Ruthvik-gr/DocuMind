"""
Unit tests for LangChain service.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock
import base64
import pickle

from app.services.langchain_service import LangChainService
from app.utils.exceptions import ProcessingError


class TestLangChainServiceInit:
    """Tests for LangChainService initialization."""

    def test_service_initializes_correctly(self):
        """Test that service initializes with correct components."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'):
            service = LangChainService()

            assert service.text_splitter is not None
            assert service.vector_stores == {}
            assert service.qa_prompt is not None


class TestLangChainServiceDocuments:
    """Tests for document creation."""

    @pytest.fixture
    def service(self):
        """Create LangChainService instance."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'):
            return LangChainService()

    def test_create_documents_splits_text(self, service):
        """Test that text is split into documents."""
        text = "This is a test document. " * 100
        metadata = {"file_id": "test-id"}

        documents = service.create_documents(text, metadata)

        assert len(documents) > 0
        assert all(doc.metadata == metadata for doc in documents)

    def test_create_documents_short_text(self, service):
        """Test creating documents from short text."""
        text = "Short text."
        metadata = {"file_id": "test-id"}

        documents = service.create_documents(text, metadata)

        assert len(documents) == 1
        assert documents[0].page_content == "Short text."


class TestLangChainServiceSerialization:
    """Tests for vector store serialization."""

    @pytest.fixture
    def service(self):
        """Create LangChainService instance."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'):
            return LangChainService()

    def test_serialize_vector_store(self, service):
        """Test vector store serialization."""
        # Use a simple serializable object instead of MagicMock
        simple_data = {"index": [1, 2, 3], "embeddings": [[0.1, 0.2]]}

        # Test serialization
        result = service._serialize_vector_store(simple_data)

        assert isinstance(result, str)
        # Should be valid base64
        decoded = base64.b64decode(result.encode('utf-8'))
        assert len(decoded) > 0

    def test_deserialize_vector_store(self, service):
        """Test vector store deserialization."""
        # Create a mock object and serialize it
        mock_data = {"test": "data"}
        pickled = pickle.dumps(mock_data)
        encoded = base64.b64encode(pickled).decode('utf-8')

        result = service._deserialize_vector_store(encoded)

        assert result == mock_data


class TestLangChainServiceVectorStore:
    """Tests for vector store operations."""

    @pytest.fixture
    def service(self):
        """Create LangChainService instance."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'):
            return LangChainService()

    def test_get_vector_store_found(self, service):
        """Test getting existing vector store."""
        mock_vs = MagicMock()
        service.vector_stores["test-id"] = mock_vs

        result = service.get_vector_store("test-id")

        assert result == mock_vs

    def test_get_vector_store_not_found(self, service):
        """Test getting non-existent vector store."""
        result = service.get_vector_store("non-existent")

        assert result is None

    @pytest.mark.asyncio
    async def test_save_vector_store_to_db(self, service):
        """Test saving vector store to database."""
        mock_vs = {"test": "data"}  # Use serializable data

        with patch('app.services.langchain_service.get_database') as mock_get_db:
            mock_collection = MagicMock()
            mock_collection.update_one = AsyncMock()
            mock_get_db.return_value = {"files": mock_collection}

            await service._save_vector_store_to_db("test-id", mock_vs)

            mock_collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_vector_store_to_db_error(self, service):
        """Test saving vector store to database with error."""
        mock_vs = MagicMock()

        with patch('app.services.langchain_service.get_database') as mock_get_db:
            mock_collection = MagicMock()
            mock_collection.update_one = AsyncMock(side_effect=Exception("DB error"))
            mock_get_db.return_value = {"files": mock_collection}

            # Should not raise, just log error
            await service._save_vector_store_to_db("test-id", mock_vs)

    @pytest.mark.asyncio
    async def test_load_vector_store_from_db_success(self, service):
        """Test loading vector store from database."""
        mock_data = {"test": "data"}
        pickled = pickle.dumps(mock_data)
        encoded = base64.b64encode(pickled).decode('utf-8')

        with patch('app.services.langchain_service.get_database') as mock_get_db:
            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value={
                "vector_store_data": encoded
            })
            mock_get_db.return_value = {"files": mock_collection}

            result = await service._load_vector_store_from_db("test-id")

            assert result == mock_data
            assert "test-id" in service.vector_stores

    @pytest.mark.asyncio
    async def test_load_vector_store_from_db_not_found(self, service):
        """Test loading vector store when not in database."""
        with patch('app.services.langchain_service.get_database') as mock_get_db:
            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_get_db.return_value = {"files": mock_collection}

            result = await service._load_vector_store_from_db("test-id")

            assert result is None

    @pytest.mark.asyncio
    async def test_load_vector_store_from_db_no_data(self, service):
        """Test loading vector store when data field is empty."""
        with patch('app.services.langchain_service.get_database') as mock_get_db:
            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value={
                "vector_store_data": None
            })
            mock_get_db.return_value = {"files": mock_collection}

            result = await service._load_vector_store_from_db("test-id")

            assert result is None

    @pytest.mark.asyncio
    async def test_load_vector_store_from_db_error(self, service):
        """Test loading vector store with database error."""
        with patch('app.services.langchain_service.get_database') as mock_get_db:
            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(side_effect=Exception("DB error"))
            mock_get_db.return_value = {"files": mock_collection}

            result = await service._load_vector_store_from_db("test-id")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_or_load_vector_store_from_memory(self, service):
        """Test get_or_load returns from memory if available."""
        mock_vs = MagicMock()
        service.vector_stores["test-id"] = mock_vs

        result = await service.get_or_load_vector_store("test-id")

        assert result == mock_vs

    @pytest.mark.asyncio
    async def test_get_or_load_vector_store_from_db(self, service):
        """Test get_or_load loads from database if not in memory."""
        mock_data = {"test": "data"}
        pickled = pickle.dumps(mock_data)
        encoded = base64.b64encode(pickled).decode('utf-8')

        with patch('app.services.langchain_service.get_database') as mock_get_db:
            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value={
                "vector_store_data": encoded
            })
            mock_get_db.return_value = {"files": mock_collection}

            result = await service.get_or_load_vector_store("test-id")

            assert result == mock_data


class TestLangChainServiceCreateVectorStore:
    """Tests for creating vector stores."""

    @pytest.fixture
    def service(self):
        """Create LangChainService instance."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'):
            return LangChainService()

    @pytest.mark.asyncio
    async def test_create_vector_store_success(self, service):
        """Test creating vector store successfully."""
        mock_vs = MagicMock()

        with patch('app.services.langchain_service.FAISS') as mock_faiss, \
             patch.object(service, '_save_vector_store_to_db', new_callable=AsyncMock):
            mock_faiss.afrom_documents = AsyncMock(return_value=mock_vs)

            result = await service.create_vector_store(
                file_id="test-id",
                text="Test document content",
                metadata={"file_id": "test-id"}
            )

            assert result == mock_vs
            assert "test-id" in service.vector_stores

    @pytest.mark.asyncio
    async def test_create_vector_store_error(self, service):
        """Test creating vector store with error."""
        with patch('app.services.langchain_service.FAISS') as mock_faiss:
            mock_faiss.afrom_documents = AsyncMock(side_effect=Exception("FAISS error"))

            with pytest.raises(ProcessingError, match="Vector store creation failed"):
                await service.create_vector_store(
                    file_id="test-id",
                    text="Test document content",
                    metadata={"file_id": "test-id"}
                )


class TestLangChainServiceQA:
    """Tests for Q&A functionality."""

    @pytest.fixture
    def service(self):
        """Create LangChainService instance."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'):
            return LangChainService()

    def test_format_docs(self, service):
        """Test formatting documents."""
        from langchain_core.documents import Document

        docs = [
            Document(page_content="First chunk"),
            Document(page_content="Second chunk")
        ]

        result = service._format_docs(docs)

        assert "First chunk" in result
        assert "Second chunk" in result
        assert "\n\n" in result

    @pytest.mark.asyncio
    async def test_ask_question_no_vector_store(self, service):
        """Test asking question without vector store."""
        with pytest.raises(ProcessingError, match="No vector store found"):
            await service.ask_question("non-existent", "What is this?")

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="LangChain internal chain mocking is complex; covered by integration tests")
    async def test_ask_question_success(self, service):
        """Test asking question successfully."""
        # This test is skipped because mocking LangChain's LCEL chain internals
        # is complex. The functionality is tested through integration tests.
        pass

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="LangChain internal chain mocking is complex; covered by integration tests")
    async def test_ask_question_with_chat_history(self, service):
        """Test asking question with chat history."""
        # This test is skipped because mocking LangChain's LCEL chain internals
        # is complex. The functionality is tested through integration tests.
        pass

    @pytest.mark.asyncio
    async def test_ask_question_error(self, service):
        """Test asking question with error."""
        mock_vs = MagicMock()
        mock_vs.as_retriever.side_effect = Exception("Retriever error")
        service.vector_stores["test-id"] = mock_vs

        with pytest.raises(ProcessingError, match="Q&A failed"):
            await service.ask_question("test-id", "What is this?")


class TestLangChainServiceStreaming:
    """Tests for streaming Q&A functionality."""

    @pytest.fixture
    def service(self):
        """Create LangChainService instance."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'):
            return LangChainService()

    @pytest.mark.asyncio
    async def test_ask_question_stream_no_vector_store(self, service):
        """Test streaming question without vector store."""
        with pytest.raises(ProcessingError, match="No vector store found"):
            async for _ in service.ask_question_stream("non-existent", "What is this?"):
                pass

    @pytest.mark.asyncio
    async def test_ask_question_stream_success(self, service):
        """Test streaming question successfully."""
        mock_vs = MagicMock()
        mock_retriever = MagicMock()
        mock_vs.as_retriever.return_value = mock_retriever

        from langchain_core.documents import Document
        mock_docs = [Document(page_content="Test content")]
        mock_retriever.ainvoke = AsyncMock(return_value=mock_docs)

        service.vector_stores["test-id"] = mock_vs

        # Create mock chunks
        class MockChunk:
            def __init__(self, content):
                self.content = content

        async def mock_astream(*args, **kwargs):
            yield MockChunk("Hello")
            yield MockChunk(" world")

        mock_chain = MagicMock()
        mock_chain.astream = mock_astream

        with patch.object(service.qa_prompt, '__or__', return_value=mock_chain):
            results = []
            async for chunk in service.ask_question_stream("test-id", "What is this?"):
                results.append(chunk)

            assert any(r["type"] == "content" for r in results)
            assert any(r["type"] == "sources" for r in results)

    @pytest.mark.asyncio
    async def test_ask_question_stream_with_history(self, service):
        """Test streaming with chat history."""
        mock_vs = MagicMock()
        mock_retriever = MagicMock()
        mock_vs.as_retriever.return_value = mock_retriever

        from langchain_core.documents import Document
        mock_docs = [Document(page_content="Test content")]
        mock_retriever.ainvoke = AsyncMock(return_value=mock_docs)

        service.vector_stores["test-id"] = mock_vs

        class MockChunk:
            def __init__(self, content):
                self.content = content

        async def mock_astream(*args, **kwargs):
            yield MockChunk("Response")

        mock_chain = MagicMock()
        mock_chain.astream = mock_astream

        with patch.object(service.qa_prompt, '__or__', return_value=mock_chain):
            chat_history = [("Previous?", "Previous answer")]
            results = []
            async for chunk in service.ask_question_stream("test-id", "Next?", chat_history):
                results.append(chunk)

            assert len(results) > 0

    @pytest.mark.asyncio
    async def test_ask_question_stream_error(self, service):
        """Test streaming with error."""
        mock_vs = MagicMock()
        mock_vs.as_retriever.side_effect = Exception("Stream error")
        service.vector_stores["test-id"] = mock_vs

        with pytest.raises(ProcessingError, match="Q&A failed"):
            async for _ in service.ask_question_stream("test-id", "What?"):
                pass
