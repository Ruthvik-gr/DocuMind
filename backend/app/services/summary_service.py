"""
Content summarization service using Groq.
"""
from groq import AsyncGroq
from datetime import datetime
import uuid
import logging
from typing import Dict

from app.config import get_settings
from app.core.database import get_database
from app.core.constants import SummaryType, COLLECTION_SUMMARIES
from app.models.summary import (
    SummaryModel,
    TokenCount,
    SummaryParameters
)
from app.utils.exceptions import ProcessingError, ExternalAPIError, DatabaseError

logger = logging.getLogger(__name__)
settings = get_settings()


class SummaryService:
    """Service for content summarization using Groq."""

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    async def generate_summary(
        self,
        file_id: str,
        user_id: str,
        text: str,
        summary_type: SummaryType
    ) -> SummaryModel:
        """
        Generate summary using Groq API.

        Args:
            file_id: File ID
            text: Text content to summarize
            summary_type: Type of summary to generate

        Returns:
            SummaryModel

        Raises:
            ProcessingError: If summarization fails
        """
        try:
            # Determine prompt based on summary type
            system_prompt = self._get_system_prompt(summary_type)

            # Truncate text if too long (to avoid token limits)
            max_chars = 15000  # Approximately 4000 tokens
            if len(text) > max_chars:
                text = text[:max_chars] + "..."

            # Call Groq API
            response = await self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=500 if summary_type == SummaryType.BRIEF else 1000
            )

            summary_text = response.choices[0].message.content
            usage = response.usage

            # Create summary model
            summary_model = SummaryModel(
                summary_id=str(uuid.uuid4()),
                user_id=user_id,
                file_id=file_id,
                summary_type=summary_type,
                content=summary_text,
                model_used=settings.GROQ_MODEL,
                token_count=TokenCount(
                    input=usage.prompt_tokens,
                    output=usage.completion_tokens,
                    total=usage.total_tokens
                ),
                parameters=SummaryParameters(
                    temperature=0.3,
                    max_tokens=500 if summary_type == SummaryType.BRIEF else 1000
                )
            )

            # Store in database
            db = get_database()
            await db[COLLECTION_SUMMARIES].insert_one(summary_model.to_dict())

            logger.info(f"Generated {summary_type.value} summary for file {file_id}")
            return summary_model

        except Exception as e:
            logger.error(f"Summarization failed for file {file_id}: {e}")
            raise ProcessingError(f"Summarization failed: {e}")

    async def get_summaries(self, file_id: str, user_id: str = None) -> list[SummaryModel]:
        """Get all summaries for a file."""
        db = get_database()
        query = {"file_id": file_id}
        if user_id:
            query["user_id"] = user_id
        cursor = db[COLLECTION_SUMMARIES].find(query)
        summaries = []

        async for doc in cursor:
            summaries.append(SummaryModel.from_dict(doc))

        return summaries

    def _get_system_prompt(self, summary_type: SummaryType) -> str:
        """Get system prompt based on summary type."""
        prompts = {
            SummaryType.BRIEF: (
                "Create a brief 2-3 sentence summary. Start directly with the content - "
                "no preface like 'Here is a summary' or 'This document discusses'. Just summarize."
            ),
            SummaryType.DETAILED: (
                "Create a comprehensive summary covering all major topics and key details. "
                "Start directly with the content - no preface like 'Here is a detailed summary' or "
                "'This document covers'. Just provide the summary."
            ),
            SummaryType.KEY_POINTS: (
                "Extract the most important points as a bullet-point list. "
                "Start directly with the bullet points - no preface like 'Here are the key points' or "
                "'The main takeaways are'. Just list the points."
            )
        }
        return prompts.get(summary_type, prompts[SummaryType.BRIEF])


# Global service instance
summary_service = SummaryService()
