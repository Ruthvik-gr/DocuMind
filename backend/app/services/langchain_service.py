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
from typing import List, Dict, Optional
import logging

from app.config import get_settings
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
            ("system", """You are a helpful assistant that answers questions based on the provided context.
Use the following context to answer the question. If you cannot find the answer in the context,
say "I don't have enough information to answer this question based on the document."

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
            logger.info(f"Created vector store for file {file_id}")
            return vector_store
        except Exception as e:
            logger.error(f"Failed to create vector store for {file_id}: {e}")
            raise ProcessingError(f"Vector store creation failed: {e}")

    def get_vector_store(self, file_id: str) -> Optional[FAISS]:
        """Get vector store for a file."""
        return self.vector_stores.get(file_id)

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


# Global service instance
langchain_service = LangChainService()
