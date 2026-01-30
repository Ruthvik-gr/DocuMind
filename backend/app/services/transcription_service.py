"""
Audio/Video transcription service using faster-whisper (local).
"""
from faster_whisper import WhisperModel
import logging
from typing import Dict, Any
from pathlib import Path
import asyncio

from app.config import get_settings
from app.utils.exceptions import ProcessingError
from app.utils.text_processors import count_words
from app.models.file import ExtractedContent, FileMetadata

logger = logging.getLogger(__name__)
settings = get_settings()


class TranscriptionService:
    """Service for audio/video transcription using local Whisper."""

    def __init__(self):
        # Use 'base' model for balance of speed and accuracy
        # Options: tiny, base, small, medium, large-v2, large-v3
        self.model = None  # Lazy load to avoid startup delay

    def _get_model(self):
        """Lazy load whisper model."""
        if self.model is None:
            logger.info("Loading Whisper model (base)...")
            # Use CPU with int8 quantization for efficiency
            self.model = WhisperModel("base", device="cpu", compute_type="int8")
            logger.info("Whisper model loaded")
        return self.model

    async def transcribe_file(self, file_path: str) -> tuple[ExtractedContent, FileMetadata]:
        """
        Transcribe audio/video file using local faster-whisper.

        Args:
            file_path: Path to audio/video file

        Returns:
            Tuple of (ExtractedContent, FileMetadata)

        Raises:
            ProcessingError: If transcription fails
        """
        try:
            # Run transcription in executor to not block async loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._transcribe_sync, file_path
            )
            return result

        except Exception as e:
            logger.error(f"Transcription failed for {file_path}: {e}")
            raise ProcessingError(f"Transcription failed: {e}")

    def _transcribe_sync(self, file_path: str) -> tuple[ExtractedContent, FileMetadata]:
        """Synchronous transcription method."""
        model = self._get_model()

        # Transcribe
        segments, info = model.transcribe(
            file_path,
            beam_size=5,
            language=None,  # Auto-detect
            vad_filter=True  # Voice activity detection
        )

        # Collect all segments
        full_text_parts = []
        for segment in segments:
            full_text_parts.append(segment.text.strip())

        full_text = " ".join(full_text_parts)
        duration = info.duration if info.duration else 0

        word_count = count_words(full_text)

        # Create extracted content
        extracted_content = ExtractedContent(
            text=full_text,
            word_count=word_count,
            language=info.language or "en",
            extraction_method="faster-whisper (local)"
        )

        # Create metadata
        file_metadata = FileMetadata(
            duration=int(duration),
            format=Path(file_path).suffix[1:],  # Remove dot from extension
            sample_rate=None,
            channels=None
        )

        logger.info(f"Transcribed file {file_path}: {word_count} words, {duration:.1f}s duration")
        return extracted_content, file_metadata

    def format_transcription_with_timestamps(self, segments: list) -> str:
        """Format transcription with inline timestamps."""
        formatted = ""
        for segment in segments:
            timestamp = self._seconds_to_timestamp(segment["start"])
            formatted += f"[{timestamp}] {segment['text']}\n"
        return formatted

    def _seconds_to_timestamp(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"


# Global service instance
transcription_service = TranscriptionService()
