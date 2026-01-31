"""
Chat/Q&A endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime
import uuid
import logging
import json

from app.services.file_service import file_service
from app.services.langchain_service import langchain_service
from app.core.database import get_database
from app.core.constants import COLLECTION_CHAT_HISTORY, COLLECTION_TIMESTAMPS, MessageRole, ProcessingStatus, FileType
from app.utils.timestamp_matcher import find_relevant_timestamp
from app.core.auth import get_current_user
from app.models.user import UserModel
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse, MessageSchema
from app.models.chat import ChatHistoryModel, Message, MessageMetadata
from app.utils.exceptions import FileNotFoundError, ProcessingError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{file_id}/ask")
async def ask_question(
    file_id: str,
    request: ChatRequest,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Ask a question about an uploaded file with streaming response.

    Returns a Server-Sent Events stream of the AI response.
    """
    user_id = current_user.id

    async def generate_stream():
        try:
            # Verify file exists and is processed
            file_model = await file_service.get_file(file_id, user_id)

            if file_model.processing_status != ProcessingStatus.COMPLETED:
                yield f"data: {json.dumps({'error': f'File is still being processed. Status: {file_model.processing_status.value}'})}\n\n"
                return

            # Get or create chat history
            db = get_database()
            chat_id = request.chat_id or f"chat-{uuid.uuid4()}"

            chat_history_doc = await db[COLLECTION_CHAT_HISTORY].find_one({
                "chat_id": chat_id,
                "user_id": user_id
            })

            if chat_history_doc:
                chat_history_model = ChatHistoryModel.from_dict(chat_history_doc)
            else:
                chat_history_model = ChatHistoryModel(
                    chat_id=chat_id,
                    user_id=user_id,
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

            # Send chat_id first
            yield f"data: {json.dumps({'chat_id': chat_id, 'type': 'start'})}\n\n"

            # Stream answer using LangChain streaming
            full_answer = ""
            source_documents = []

            async for chunk in langchain_service.ask_question_stream(
                file_id=file_id,
                question=request.question,
                chat_history=formatted_history
            ):
                if chunk["type"] == "content":
                    full_answer += chunk["data"]
                    yield f"data: {json.dumps({'content': chunk['data'], 'type': 'content'})}\n\n"
                elif chunk["type"] == "sources":
                    source_documents = chunk["data"]

            # Create user message
            user_message = Message(
                message_id=f"msg-{uuid.uuid4()}",
                role=MessageRole.USER,
                content=request.question,
                timestamp=datetime.utcnow(),
                token_count=len(request.question.split())
            )

            # Create assistant message
            assistant_message = Message(
                message_id=f"msg-{uuid.uuid4()}",
                role=MessageRole.ASSISTANT,
                content=full_answer,
                timestamp=datetime.utcnow(),
                token_count=len(full_answer.split()),
                metadata=MessageMetadata(
                    source_chunks=source_documents,
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

            # Find suggested timestamp for audio/video files
            suggested_timestamp = None
            if file_model.file_type in [FileType.AUDIO, FileType.VIDEO]:
                # Get timestamps for this file
                timestamps_doc = await db[COLLECTION_TIMESTAMPS].find_one({
                    "file_id": file_id
                })
                if timestamps_doc and timestamps_doc.get("timestamps"):
                    timestamps_list = timestamps_doc["timestamps"]
                    suggested_timestamp = find_relevant_timestamp(
                        answer=full_answer,
                        source_chunks=source_documents,
                        timestamps=timestamps_list
                    )

            # Send completion event with suggested timestamp
            completion_data = {
                'type': 'done',
                'sources': source_documents
            }
            if suggested_timestamp is not None:
                completion_data['suggested_timestamp'] = suggested_timestamp

            yield f"data: {json.dumps(completion_data)}\n\n"

        except FileNotFoundError:
            yield f"data: {json.dumps({'error': f'File not found: {file_id}'})}\n\n"
        except ProcessingError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        except Exception as e:
            logger.error(f"Q&A streaming failed for file {file_id}: {e}")
            yield f"data: {json.dumps({'error': 'Failed to process question'})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/{file_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    file_id: str,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get chat history for a file.
    """
    try:
        db = get_database()
        doc = await db[COLLECTION_CHAT_HISTORY].find_one({
            "file_id": file_id,
            "user_id": current_user.id
        })

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
