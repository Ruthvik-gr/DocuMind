"""
LangChain service for Q&A functionality using Groq and Pinecone.
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Optional, AsyncGenerator
import logging
from datetime import datetime

from app.config import get_settings
from app.core.database import get_database
from app.core.constants import COLLECTION_FILES
from app.utils.exceptions import ProcessingError

logger = logging.getLogger(__name__)
settings = get_settings()


class LangChainService:
    """Service for LangChain-powered Q&A using Groq and Pinecone."""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        # Lazy load embeddings to avoid startup delay
        self._embeddings = None

        # Use Groq for LLM (lightweight, no model download)
        self.llm = ChatGroq(
            model_name=settings.GROQ_MODEL,
            temperature=settings.GROQ_TEMPERATURE,
            groq_api_key=settings.GROQ_API_KEY
        )

        # Initialize Pinecone (lightweight, just API connection)
        self.pinecone_client = None
        self.pinecone_index = None
        if settings.PINECONE_API_KEY:
            try:
                self.pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
                self._ensure_index_exists()
                self.pinecone_index = self.pinecone_client.Index(settings.PINECONE_INDEX_NAME)
                logger.info(f"Connected to Pinecone index: {settings.PINECONE_INDEX_NAME}")
            except Exception as e:
                logger.error(f"Failed to initialize Pinecone: {e}")

        # Q&A prompt template
        self.qa_prompt = ChatPromptTemplate.from_messages([
            ("system", """Answer questions using only the provided context. Give direct, concise answers without any preface like "Based on the document", "According to the context", or "The document states". Just provide the answer directly.

If you cannot find the answer in the context, simply say "I couldn't find this information in the document."

Context:
{context}"""),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{question}")
        ])

    @property
    def embeddings(self):
        """Lazy load HuggingFace embeddings model."""
        if self._embeddings is None:
            logger.info("Loading HuggingFace embeddings model (sentence-transformers/all-MiniLM-L6-v2)...")
            self._embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info("HuggingFace embeddings model loaded")
        return self._embeddings

    def _ensure_index_exists(self):
        """Create Pinecone index if it doesn't exist."""
        try:
            existing_indexes = [idx.name for idx in self.pinecone_client.list_indexes()]
            if settings.PINECONE_INDEX_NAME not in existing_indexes:
                logger.info(f"Creating Pinecone index: {settings.PINECONE_INDEX_NAME}")
                self.pinecone_client.create_index(
                    name=settings.PINECONE_INDEX_NAME,
                    dimension=384,  # all-MiniLM-L6-v2 produces 384-dim vectors
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logger.info(f"Created Pinecone index: {settings.PINECONE_INDEX_NAME}")
        except Exception as e:
            logger.error(f"Error ensuring Pinecone index exists: {e}")
            raise

    def is_configured(self) -> bool:
        """Check if Pinecone is properly configured."""
        return self.pinecone_client is not None and settings.PINECONE_API_KEY

    def create_documents(self, text: str, metadata: dict) -> List[Document]:
        """
        Split text into chunks and create LangChain documents.

        Args:
            text: Text to split
            metadata: Metadata to attach to documents

        Returns:
            List of Document objects
        """
        chunks = self.text_splitter.split_text(text)
        documents = [
            Document(page_content=chunk, metadata=metadata)
            for chunk in chunks
        ]
        logger.info(f"Created {len(documents)} document chunks")
        return documents

    async def create_vector_store(
        self,
        file_id: str,
        text: str,
        metadata: dict
    ) -> PineconeVectorStore:
        """
        Create and store vectors in Pinecone for a file.

        Args:
            file_id: File ID (used as namespace)
            text: Text content
            metadata: Document metadata

        Returns:
            PineconeVectorStore instance
        """
        if not self.is_configured():
            raise ProcessingError("Pinecone is not configured. Please set PINECONE_API_KEY.")

        try:
            documents = self.create_documents(text, metadata)

            # Add file_id to each document's metadata for filtering
            for doc in documents:
                doc.metadata["file_id"] = file_id

            # Create vector store in Pinecone using file_id as namespace
            vector_store = PineconeVectorStore.from_documents(
                documents=documents,
                embedding=self.embeddings,
                index_name=settings.PINECONE_INDEX_NAME,
                namespace=file_id,
                pinecone_api_key=settings.PINECONE_API_KEY
            )

            # Update file document to indicate vectors are stored
            db = get_database()
            result = await db[COLLECTION_FILES].update_one(
                {"file_id": file_id},
                {"$set": {
                    "vector_store_type": "pinecone",
                    "vector_store_namespace": file_id,
                    "vector_store_updated_at": datetime.utcnow(),
                    "vector_count": len(documents)
                }}
            )

            if result.matched_count == 0:
                logger.warning(f"No document found to update for file {file_id}")

            logger.info(f"Created vector store in Pinecone for file {file_id} with {len(documents)} vectors")
            return vector_store

        except Exception as e:
            logger.error(f"Failed to create vector store for {file_id}: {e}")
            raise ProcessingError(f"Vector store creation failed: {e}")

    def get_vector_store(self, file_id: str) -> Optional[PineconeVectorStore]:
        """Get vector store for a file from Pinecone."""
        if not self.is_configured():
            return None

        try:
            # Create a PineconeVectorStore instance pointing to the file's namespace
            return PineconeVectorStore(
                index_name=settings.PINECONE_INDEX_NAME,
                embedding=self.embeddings,
                namespace=file_id
            )
        except Exception as e:
            logger.error(f"Failed to get vector store for {file_id}: {e}")
            return None

    async def get_or_load_vector_store(self, file_id: str) -> Optional[PineconeVectorStore]:
        """Get vector store from Pinecone."""
        if not self.is_configured():
            logger.warning("Pinecone is not configured")
            return None

        # With Pinecone, we just need to create a reference to the namespace
        # The vectors are already stored in the cloud
        return self.get_vector_store(file_id)

    async def delete_vector_store(self, file_id: str):
        """Delete all vectors for a file from Pinecone."""
        if not self.is_configured():
            return

        try:
            # Delete all vectors in the namespace
            self.pinecone_index.delete(delete_all=True, namespace=file_id)
            logger.info(f"Deleted vector store from Pinecone for file {file_id}")
        except Exception as e:
            logger.error(f"Failed to delete vector store for {file_id}: {e}")

    def _format_docs(self, docs: List[Document]) -> str:
        """Format documents into a single string."""
        return "\n\n".join(doc.page_content for doc in docs)

    async def ask_question(
        self,
        file_id: str,
        question: str,
        chat_history: List[tuple] = None
    ) -> Dict[str, any]:
        """
        Ask a question about a file using LangChain and Groq.

        Args:
            file_id: File ID
            question: User question
            chat_history: Previous chat history as list of (question, answer) tuples

        Returns:
            Dict with answer and source documents

        Raises:
            ProcessingError: If Q&A fails
        """
        vector_store = await self.get_or_load_vector_store(file_id)
        if not vector_store:
            raise ProcessingError(f"No vector store found for file {file_id}")

        try:
            # Get retriever
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4}
            )

            # Get relevant documents
            docs = await retriever.ainvoke(question)
            context = self._format_docs(docs)

            # Format chat history for the prompt
            formatted_history = []
            if chat_history:
                for q, a in chat_history:
                    formatted_history.append(("human", q))
                    formatted_history.append(("assistant", a))

            # Create the chain using LCEL
            chain = self.qa_prompt | self.llm | StrOutputParser()

            # Invoke the chain
            answer = await chain.ainvoke({
                "context": context,
                "question": question,
                "chat_history": formatted_history
            })

            return {
                "answer": answer,
                "source_documents": [doc.page_content for doc in docs]
            }

        except Exception as e:
            logger.error(f"Q&A failed for file {file_id}: {e}")
            raise ProcessingError(f"Q&A failed: {e}")

    async def ask_question_stream(
        self,
        file_id: str,
        question: str,
        chat_history: List[tuple] = None
    ) -> AsyncGenerator[Dict[str, any], None]:
        """
        Ask a question with streaming response.

        Args:
            file_id: File ID
            question: User question
            chat_history: Previous chat history

        Yields:
            Dicts with 'type' (content/sources) and 'data'
        """
        vector_store = await self.get_or_load_vector_store(file_id)
        if not vector_store:
            raise ProcessingError(f"No vector store found for file {file_id}")

        try:
            # Get retriever
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4}
            )

            # Get relevant documents
            docs = await retriever.ainvoke(question)
            context = self._format_docs(docs)

            # Format chat history
            formatted_history = []
            if chat_history:
                for q, a in chat_history:
                    formatted_history.append(("human", q))
                    formatted_history.append(("assistant", a))

            # Create chain
            chain = self.qa_prompt | self.llm

            # Stream the response
            async for chunk in chain.astream({
                "context": context,
                "question": question,
                "chat_history": formatted_history
            }):
                if hasattr(chunk, 'content') and chunk.content:
                    yield {"type": "content", "data": chunk.content}

            # Yield sources at the end
            yield {"type": "sources", "data": [doc.page_content for doc in docs]}

        except Exception as e:
            logger.error(f"Streaming Q&A failed for file {file_id}: {e}")
            raise ProcessingError(f"Q&A failed: {e}")


# Global service instance
langchain_service = LangChainService()
