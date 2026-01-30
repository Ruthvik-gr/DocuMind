"""
Timestamp extraction service for audio/video files using Groq.
"""
from groq import AsyncGroq
import json
import uuid
import logging
from datetime import datetime
from typing import List

from app.config import get_settings
from app.core.database import get_database
from app.core.constants import COLLECTION_TIMESTAMPS
from app.models.timestamp import (
    TimestampModel,
    TimestampEntry,
    ExtractionMetadata
)
from app.utils.exceptions import ProcessingError, ExternalAPIError

logger = logging.getLogger(__name__)
settings = get_settings()


class TimestampService:
    """Service for timestamp extraction from transcriptions using Groq."""

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    async def extract_timestamps(
        self,
        file_id: str,
        transcription: str,
        duration: int
    ) -> TimestampModel:
        """
        Extract topics and timestamps from transcription using Groq LLM.

        Args:
            file_id: File ID
            transcription: Full transcription text
            duration: Total duration in seconds

        Returns:
            TimestampModel with extracted timestamps

        Raises:
            ProcessingError: If extraction fails
        """
        try:
            system_prompt = """You are analyzing a transcription from an audio/video file.
Identify major topics and their approximate start times.

Return a JSON array of topics with this structure:
[
    {
        "time": 120,
        "topic": "Topic Name",
        "description": "Brief description",
        "keywords": ["keyword1", "keyword2"]
    }
]

Guidelines:
- Identify 5-15 major topics depending on content length
- Topics should be meaningful segments, not every sentence
- Estimate times based on content progression
- Provide concise but informative descriptions
"""

            # Truncate transcription if too long
            max_chars = 10000
            truncated_text = transcription[:max_chars] if len(transcription) > max_chars else transcription

            response = await self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Transcription (duration: {duration}s):\n\n{truncated_text}"}
                ],
                temperature=0.2,
                max_tokens=1500
            )

            # Parse response
            content = response.choices[0].message.content

            # Extract JSON from response
            timestamps_data = self._parse_json_response(content)

            # Create timestamp entries
            timestamp_entries = []
            for idx, item in enumerate(timestamps_data):
                entry = TimestampEntry(
                    timestamp_entry_id=f"ts-entry-{uuid.uuid4()}",
                    time=item.get("time", 0),
                    topic=item.get("topic", f"Topic {idx + 1}"),
                    description=item.get("description", ""),
                    keywords=item.get("keywords", []),
                    confidence=0.8  # Default confidence
                )
                timestamp_entries.append(entry)

            # Create timestamp model
            timestamp_model = TimestampModel(
                timestamp_id=str(uuid.uuid4()),
                file_id=file_id,
                timestamps=timestamp_entries,
                extraction_metadata=ExtractionMetadata(
                    total_topics=len(timestamp_entries),
                    extraction_method="LLM-based",
                    model_used=settings.GROQ_MODEL
                )
            )

            # Store in database
            db = get_database()
            await db[COLLECTION_TIMESTAMPS].insert_one(timestamp_model.to_dict())

            logger.info(f"Extracted {len(timestamp_entries)} timestamps for file {file_id}")
            return timestamp_model

        except Exception as e:
            logger.error(f"Timestamp extraction failed for file {file_id}: {e}")
            raise ProcessingError(f"Timestamp extraction failed: {e}")

    async def get_timestamps(self, file_id: str) -> TimestampModel:
        """Get timestamps for a file."""
        db = get_database()
        doc = await db[COLLECTION_TIMESTAMPS].find_one({"file_id": file_id})

        if not doc:
            return None

        return TimestampModel.from_dict(doc)

    def _parse_json_response(self, content: str) -> List[dict]:
        """Parse JSON from LLM response."""
        try:
            # Try to find JSON array in the response
            start = content.find('[')
            end = content.rfind(']') + 1

            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                # If no JSON found, return empty list
                logger.warning("No JSON array found in response")
                return []

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            return []


# Global service instance
timestamp_service = TimestampService()
