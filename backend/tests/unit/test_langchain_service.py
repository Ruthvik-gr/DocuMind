"""
Unit tests for LangChain service with Pinecone.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.langchain_service import LangChainService
from app.utils.exceptions import ProcessingError


class TestLangChainServiceInit:
    """Tests for LangChainService initialization."""

    def test_service_initializes_correctly(self):
        """Test that service initializes with correct components."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'), \
             patch('app.services.langchain_service.Pinecone'):
            service = LangChainService()

            assert service.text_splitter is not None
            assert service.qa_prompt is not None

    def test_service_without_pinecone_api_key(self):
        """Test that service works without Pinecone API key."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'), \
             patch('app.services.langchain_service.settings') as mock_settings:
            mock_settings.PINECONE_API_KEY = ""
            mock_settings.GROQ_API_KEY = "test-key"
            mock_settings.GROQ_MODEL = "test-model"
            mock_settings.GROQ_TEMPERATURE = 0.3

            service = LangChainService()

            assert service.pinecone_client is None
            assert not service.is_configured()


class TestLangChainServiceDocuments:
    """Tests for document creation."""

    @pytest.fixture
    def service(self):
        """Create LangChainService instance."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'), \
             patch('app.services.langchain_service.Pinecone'):
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


class TestLangChainServicePinecone:
    """Tests for Pinecone vector store operations."""

    @pytest.fixture
    def service(self):
        """Create LangChainService instance with mocked Pinecone."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'), \
             patch('app.services.langchain_service.Pinecone') as mock_pinecone:
            mock_pinecone.return_value.list_indexes.return_value = []
            service = LangChainService()
            service.pinecone_client = mock_pinecone.return_value
            return service

    def test_is_configured_true(self, service):
        """Test is_configured returns True when Pinecone is set up."""
        with patch('app.services.langchain_service.settings') as mock_settings:
            mock_settings.PINECONE_API_KEY = "test-api-key"
            assert service.is_configured()

    def test_is_configured_false_no_client(self):
        """Test is_configured returns False when no client."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'), \
             patch('app.services.langchain_service.settings') as mock_settings:
            mock_settings.PINECONE_API_KEY = ""
            mock_settings.GROQ_API_KEY = "test-key"
            mock_settings.GROQ_MODEL = "test-model"
            mock_settings.GROQ_TEMPERATURE = 0.3

            service = LangChainService()
            assert not service.is_configured()

    def test_get_vector_store_not_configured(self):
        """Test getting vector store when not configured."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'), \
             patch('app.services.langchain_service.settings') as mock_settings:
            mock_settings.PINECONE_API_KEY = ""
            mock_settings.GROQ_API_KEY = "test-key"
            mock_settings.GROQ_MODEL = "test-model"
            mock_settings.GROQ_TEMPERATURE = 0.3

            service = LangChainService()
            result = service.get_vector_store("test-id")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_or_load_vector_store_not_configured(self):
        """Test get_or_load when not configured."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'), \
             patch('app.services.langchain_service.settings') as mock_settings:
            mock_settings.PINECONE_API_KEY = ""
            mock_settings.GROQ_API_KEY = "test-key"
            mock_settings.GROQ_MODEL = "test-model"
            mock_settings.GROQ_TEMPERATURE = 0.3

            service = LangChainService()
            result = await service.get_or_load_vector_store("test-id")
            assert result is None


class TestLangChainServiceCreateVectorStore:
    """Tests for creating vector stores."""

    @pytest.fixture
    def service(self):
        """Create LangChainService instance."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'), \
             patch('app.services.langchain_service.Pinecone') as mock_pinecone:
            mock_pinecone.return_value.list_indexes.return_value = []
            service = LangChainService()
            service.pinecone_client = mock_pinecone.return_value
            return service

    @pytest.mark.asyncio
    async def test_create_vector_store_not_configured(self):
        """Test creating vector store when Pinecone not configured."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'), \
             patch('app.services.langchain_service.settings') as mock_settings:
            mock_settings.PINECONE_API_KEY = ""
            mock_settings.GROQ_API_KEY = "test-key"
            mock_settings.GROQ_MODEL = "test-model"
            mock_settings.GROQ_TEMPERATURE = 0.3

            service = LangChainService()

            with pytest.raises(ProcessingError, match="Pinecone is not configured"):
                await service.create_vector_store(
                    file_id="test-id",
                    text="Test document content",
                    metadata={"file_id": "test-id"}
                )

    @pytest.mark.asyncio
    async def test_create_vector_store_success(self, service):
        """Test creating vector store successfully."""
        mock_vs = MagicMock()

        with patch('app.services.langchain_service.PineconeVectorStore') as mock_pvs, \
             patch('app.services.langchain_service.get_database') as mock_get_db, \
             patch('app.services.langchain_service.settings') as mock_settings:
            mock_settings.PINECONE_API_KEY = "test-api-key"
            mock_settings.PINECONE_INDEX_NAME = "test-index"
            mock_pvs.from_documents.return_value = mock_vs

            mock_collection = MagicMock()
            mock_result = MagicMock()
            mock_result.matched_count = 1
            mock_collection.update_one = AsyncMock(return_value=mock_result)
            mock_get_db.return_value = {"files": mock_collection}

            result = await service.create_vector_store(
                file_id="test-id",
                text="Test document content",
                metadata={"file_id": "test-id"}
            )

            assert result == mock_vs
            mock_pvs.from_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_vector_store_error(self, service):
        """Test creating vector store with error."""
        with patch('app.services.langchain_service.PineconeVectorStore') as mock_pvs, \
             patch('app.services.langchain_service.settings') as mock_settings:
            mock_settings.PINECONE_API_KEY = "test-api-key"
            mock_settings.PINECONE_INDEX_NAME = "test-index"
            mock_pvs.from_documents.side_effect = Exception("Pinecone error")

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
             patch('app.services.langchain_service.ChatGroq'), \
             patch('app.services.langchain_service.Pinecone'):
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
    async def test_ask_question_no_vector_store(self):
        """Test asking question without vector store."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'), \
             patch('app.services.langchain_service.settings') as mock_settings:
            mock_settings.PINECONE_API_KEY = ""
            mock_settings.GROQ_API_KEY = "test-key"
            mock_settings.GROQ_MODEL = "test-model"
            mock_settings.GROQ_TEMPERATURE = 0.3

            service = LangChainService()

            with pytest.raises(ProcessingError, match="No vector store found"):
                await service.ask_question("non-existent", "What is this?")

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="LangChain internal chain mocking is complex; covered by integration tests")
    async def test_ask_question_success(self, service):
        """Test asking question successfully."""
        pass

    @pytest.mark.asyncio
    async def test_ask_question_error(self, service):
        """Test asking question with error."""
        mock_vs = MagicMock()
        mock_vs.as_retriever.side_effect = Exception("Retriever error")

        with patch.object(service, 'get_or_load_vector_store', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_vs

            with pytest.raises(ProcessingError, match="Q&A failed"):
                await service.ask_question("test-id", "What is this?")


class TestLangChainServiceStreaming:
    """Tests for streaming Q&A functionality."""

    @pytest.fixture
    def service(self):
        """Create LangChainService instance."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'), \
             patch('app.services.langchain_service.Pinecone'):
            return LangChainService()

    @pytest.mark.asyncio
    async def test_ask_question_stream_no_vector_store(self):
        """Test streaming question without vector store."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'), \
             patch('app.services.langchain_service.settings') as mock_settings:
            mock_settings.PINECONE_API_KEY = ""
            mock_settings.GROQ_API_KEY = "test-key"
            mock_settings.GROQ_MODEL = "test-model"
            mock_settings.GROQ_TEMPERATURE = 0.3

            service = LangChainService()

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

        # Create mock chunks
        class MockChunk:
            def __init__(self, content):
                self.content = content

        async def mock_astream(*args, **kwargs):
            yield MockChunk("Hello")
            yield MockChunk(" world")

        mock_chain = MagicMock()
        mock_chain.astream = mock_astream

        with patch.object(service, 'get_or_load_vector_store', new_callable=AsyncMock) as mock_get, \
             patch.object(service.qa_prompt, '__or__', return_value=mock_chain):
            mock_get.return_value = mock_vs

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

        class MockChunk:
            def __init__(self, content):
                self.content = content

        async def mock_astream(*args, **kwargs):
            yield MockChunk("Response")

        mock_chain = MagicMock()
        mock_chain.astream = mock_astream

        with patch.object(service, 'get_or_load_vector_store', new_callable=AsyncMock) as mock_get, \
             patch.object(service.qa_prompt, '__or__', return_value=mock_chain):
            mock_get.return_value = mock_vs

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

        with patch.object(service, 'get_or_load_vector_store', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_vs

            with pytest.raises(ProcessingError, match="Q&A failed"):
                async for _ in service.ask_question_stream("test-id", "What?"):
                    pass


class TestLangChainServiceDeleteVectorStore:
    """Tests for deleting vector stores."""

    @pytest.fixture
    def service(self):
        """Create LangChainService instance with mocked Pinecone."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'), \
             patch('app.services.langchain_service.Pinecone') as mock_pinecone:
            mock_pinecone.return_value.list_indexes.return_value = []
            service = LangChainService()
            service.pinecone_client = mock_pinecone.return_value
            service.pinecone_index = MagicMock()
            return service

    @pytest.mark.asyncio
    async def test_delete_vector_store_success(self, service):
        """Test deleting vector store successfully."""
        with patch('app.services.langchain_service.settings') as mock_settings:
            mock_settings.PINECONE_API_KEY = "test-api-key"

            await service.delete_vector_store("test-id")

            service.pinecone_index.delete.assert_called_once_with(
                delete_all=True,
                namespace="test-id"
            )

    @pytest.mark.asyncio
    async def test_delete_vector_store_not_configured(self):
        """Test deleting vector store when not configured."""
        with patch('app.services.langchain_service.HuggingFaceEmbeddings'), \
             patch('app.services.langchain_service.ChatGroq'), \
             patch('app.services.langchain_service.settings') as mock_settings:
            mock_settings.PINECONE_API_KEY = ""
            mock_settings.GROQ_API_KEY = "test-key"
            mock_settings.GROQ_MODEL = "test-model"
            mock_settings.GROQ_TEMPERATURE = 0.3

            service = LangChainService()

            # Should not raise, just return
            await service.delete_vector_store("test-id")
