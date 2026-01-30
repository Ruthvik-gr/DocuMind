"""
Chat/Q&A endpoints.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
import uuid
import logging

from app.services.file_service import file_service
from app.services.langchain_service import langchain_service
from app.core.database import get_database
from app.core.constants import COLLECTION_CHAT_HISTORY, MessageRole, ProcessingStatus
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse, MessageSchema
from app.models.chat import ChatHistoryModel, Message, MessageMetadata
from app.utils.exceptions import FileNotFoundError, ProcessingError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{file_id}/ask", response_model=ChatResponse)
async def ask_question(file_id: str, request: ChatRequest):
    """
    Ask a question about an uploaded file.

    The system will use the file's extracted content to provide an answer.
    """
    try:
        # Verify file exists and is processed
        file_model = await file_service.get_file(file_id)

        if file_model.processing_status != ProcessingStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"File is still being processed. Status: {file_model.processing_status.value}"
            )

        # Get or create chat history
        db = get_database()
        chat_id = request.chat_id or f"chat-{uuid.uuid4()}"

        chat_history_doc = await db[COLLECTION_CHAT_HISTORY].find_one({"chat_id": chat_id})

        if chat_history_doc:
            chat_history_model = ChatHistoryModel.from_dict(chat_history_doc)
        else:
            chat_history_model = ChatHistoryModel(
                chat_id=chat_id,
                file_id=file_id,
                messages=[],
                total_messages=0,
                total_tokens=0
            )

        # Convert previous messages to format expected by LangChain
        formatted_history = []
        for msg in chat_history_model.messages:
            if msg.role == MessageRole.USER:
                formatted_history.append((msg.content, ""))
            elif msg.role == MessageRole.ASSISTANT and formatted_history:
                formatted_history[-1] = (formatted_history[-1][0], msg.content)

        # Ask question using LangChain
        result = await langchain_service.ask_question(
            file_id=file_id,
            question=request.question,
            chat_history=formatted_history
        )

        # Create user message
        user_message = Message(
            message_id=f"msg-{uuid.uuid4()}",
            role=MessageRole.USER,
            content=request.question,
            timestamp=datetime.utcnow(),
            token_count=len(request.question.split())  # Rough estimate
        )

        # Create assistant message
        assistant_message = Message(
            message_id=f"msg-{uuid.uuid4()}",
            role=MessageRole.ASSISTANT,
            content=result["answer"],
            timestamp=datetime.utcnow(),
            token_count=len(result["answer"].split()),  # Rough estimate
            metadata=MessageMetadata(
                source_chunks=result["source_documents"],
                model=None,
                confidence=None
            )
        )

        # Update chat history
        chat_history_model.messages.extend([user_message, assistant_message])
        chat_history_model.total_messages = len(chat_history_model.messages)
        chat_history_model.total_tokens += (
            user_message.token_count + assistant_message.token_count
        )
        chat_history_model.updated_at = datetime.utcnow()

        # Save to database
        await db[COLLECTION_CHAT_HISTORY].update_one(
            {"chat_id": chat_id},
            {"$set": chat_history_model.to_dict()},
            upsert=True
        )

        return ChatResponse(
            answer=result["answer"],
            chat_id=chat_id,
            sources=result["source_documents"],
            timestamp=datetime.utcnow()
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
    except ProcessingError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Q&A failed for file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process question")


@router.get("/{file_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(file_id: str):
    """
    Get chat history for a file.
    """
    try:
        db = get_database()
        doc = await db[COLLECTION_CHAT_HISTORY].find_one({"file_id": file_id})

        if not doc:
            # Return empty history if none exists
            return ChatHistoryResponse(
                chat_id=f"chat-{uuid.uuid4()}",
                file_id=file_id,
                messages=[],
                total_messages=0,
                total_tokens=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

        chat_history = ChatHistoryModel.from_dict(doc)

        # Convert to response schema
        messages = [
            MessageSchema(
                message_id=msg.message_id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                token_count=msg.token_count,
                metadata=msg.metadata.model_dump() if msg.metadata else None
            )
            for msg in chat_history.messages
        ]

        return ChatHistoryResponse(
            chat_id=chat_history.chat_id,
            file_id=chat_history.file_id,
            messages=messages,
            total_messages=chat_history.total_messages,
            total_tokens=chat_history.total_tokens,
            created_at=chat_history.created_at,
            updated_at=chat_history.updated_at
        )

    except Exception as e:
        logger.error(f"Failed to get chat history for file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")
