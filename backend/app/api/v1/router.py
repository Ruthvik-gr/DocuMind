"""
Main API router for v1 endpoints.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import files, chat, summarization, timestamps

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(summarization.router, prefix="/summaries", tags=["summaries"])
api_router.include_router(timestamps.router, prefix="/timestamps", tags=["timestamps"])
