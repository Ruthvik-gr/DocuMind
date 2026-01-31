"""
LangChain service for Q&A functionality using Groq.
"""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict, Optional, AsyncGenerator
import logging
import pickle
import base64
from datetime import datetime

from app.config import get_settings
from app.core.database import get_database
from app.core.constants import COLLECTION_FILES
from app.utils.exceptions import ProcessingError

logger = logging.getLogger(__name__)
settings = get_settings()


class LangChainService:
    """Service for LangChain-powered Q&A using Groq."""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        # Use HuggingFace embeddings (runs locally, no API needed)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        # Use Groq for LLM
        self.llm = ChatGroq(
            model_name=settings.GROQ_MODEL,
            temperature=settings.GROQ_TEMPERATURE,
            groq_api_key=settings.GROQ_API_KEY
        )
        # Store vector stores in memory, keyed by file_id
        self.vector_stores: Dict[str, FAISS] = {}

        # Q&A prompt template
        self.qa_prompt = ChatPromptTemplate.from_messages([
            ("system", """Answer questions using only the provided context. Give direct, concise answers without any preface like "Based on the document", "According to the context", or "The document states". Just provide the answer directly.

If you cannot find the answer in the context, simply say "I couldn't find this information in the document."

Context:
{context}"""),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{question}")
        ])

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

    def _serialize_vector_store(self, vector_store: FAISS) -> str:
        """Serialize FAISS vector store to base64 string for MongoDB storage."""
        pickled = pickle.dumps(vector_store)
        return base64.b64encode(pickled).decode('utf-8')

    def _deserialize_vector_store(self, data: str) -> FAISS:
        """Deserialize FAISS vector store from base64 string."""
        pickled = base64.b64decode(data.encode('utf-8'))
        return pickle.loads(pickled)

    async def _save_vector_store_to_db(self, file_id: str, vector_store: FAISS):
        """Save vector store to files collection in MongoDB."""
        try:
            db = get_database()
            serialized = self._serialize_vector_store(vector_store)
            await db[COLLECTION_FILES].update_one(
                {"file_id": file_id},
                {"$set": {
                    "vector_store_data": serialized,
                    "vector_store_updated_at": datetime.utcnow()
                }}
            )
            logger.info(f"Saved vector store to DB for file {file_id}")
        except Exception as e:
            logger.error(f"Failed to save vector store to DB for {file_id}: {e}")
            # Don't raise - vector store is still in memory

    async def _load_vector_store_from_db(self, file_id: str) -> Optional[FAISS]:
        """Load vector store from files collection in MongoDB."""
        try:
            db = get_database()
            doc = await db[COLLECTION_FILES].find_one(
                {"file_id": file_id},
                {"vector_store_data": 1}
            )
            if doc and doc.get("vector_store_data"):
                vector_store = self._deserialize_vector_store(doc["vector_store_data"])
                # Cache in memory
                self.vector_stores[file_id] = vector_store
                logger.info(f"Loaded vector store from DB for file {file_id}")
                return vector_store
            return None
        except Exception as e:
            logger.error(f"Failed to load vector store from DB for {file_id}: {e}")
            return None

    async def create_vector_store(
        self,
        file_id: str,
        text: str,
        metadata: dict
    ) -> FAISS:
        """
        Create and store vector store for a file.

        Args:
            file_id: File ID
            text: Text content
            metadata: Document metadata

        Returns:
            FAISS vector store
        """
        try:
            documents = self.create_documents(text, metadata)
            vector_store = await FAISS.afrom_documents(documents, self.embeddings)
            self.vector_stores[file_id] = vector_store

            # Persist to MongoDB
            await self._save_vector_store_to_db(file_id, vector_store)

            logger.info(f"Created vector store for file {file_id}")
            return vector_store
        except Exception as e:
            logger.error(f"Failed to create vector store for {file_id}: {e}")
            raise ProcessingError(f"Vector store creation failed: {e}")

    def get_vector_store(self, file_id: str) -> Optional[FAISS]:
        """Get vector store for a file from memory cache."""
        return self.vector_stores.get(file_id)

    async def get_or_load_vector_store(self, file_id: str) -> Optional[FAISS]:
        """Get vector store from memory or load from MongoDB."""
        # Check memory first
        vector_store = self.vector_stores.get(file_id)
        if vector_store:
            return vector_store

        # Try loading from database
        return await self._load_vector_store_from_db(file_id)

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
        vector_store = self.get_vector_store(file_id)
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
        vector_store = self.get_vector_store(file_id)
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
