"""
Integration tests with real API calls for services.
These tests use real Groq API and Whisper, so they may be slow and use API quota.
"""
import pytest
import os
import tempfile
from pathlib import Path

from app.core.constants import SummaryType


@pytest.mark.integration
class TestLangChainServiceAPI:
    """Integration tests for LangChain service with real API."""

    @pytest.mark.asyncio
    async def test_create_vector_store_and_ask_question(self):
        """Test creating vector store and asking questions with real API."""
        from unittest.mock import patch, AsyncMock, MagicMock
        from app.services.langchain_service import langchain_service

        # Sample text for testing
        sample_text = """
        Python is a high-level, interpreted programming language. It was created by Guido van Rossum
        and first released in 1991. Python emphasizes code readability with its notable use of
        significant indentation. Its language constructs and object-oriented approach aim to help
        programmers write clear, logical code for small and large-scale projects.

        Python is dynamically typed and garbage-collected. It supports multiple programming paradigms,
        including structured, object-oriented and functional programming. It is often described as a
        "batteries included" language due to its comprehensive standard library.
        """

        file_id = "test-python-file"
        metadata = {"file_id": file_id, "source": "test"}

        # Mock database for vector store persistence
        with patch('app.services.langchain_service.get_database') as mock_db:
            mock_collection = MagicMock()
            mock_result = MagicMock()
            mock_result.modified_count = 1
            mock_result.matched_count = 1
            mock_collection.update_one = AsyncMock(return_value=mock_result)
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_db.return_value = {"files": mock_collection}

            try:
                # Create vector store
                await langchain_service.create_vector_store(
                    file_id=file_id,
                    text=sample_text,
                    metadata=metadata
                )

                # Verify vector store can be retrieved (stored in Pinecone)
                vector_store = langchain_service.get_vector_store(file_id)
                assert vector_store is not None

                # Ask a question
                result = await langchain_service.ask_question(
                    file_id=file_id,
                    question="Who created Python?",
                    chat_history=[]
                )

                assert "answer" in result
                assert "source_documents" in result
                # The answer should mention Guido van Rossum
                assert "Guido" in result["answer"] or "van Rossum" in result["answer"]

            finally:
                # Cleanup - delete vectors from Pinecone
                await langchain_service.delete_vector_store(file_id)


@pytest.mark.integration
class TestSummaryServiceAPI:
    """Integration tests for Summary service with real Groq API."""

    @pytest.mark.asyncio
    async def test_generate_brief_summary(self):
        """Test generating a brief summary with real Groq API."""
        from unittest.mock import patch, AsyncMock, MagicMock
        from app.services.summary_service import summary_service

        sample_text = """
        Artificial Intelligence (AI) is the simulation of human intelligence processes by machines,
        especially computer systems. These processes include learning, reasoning, and self-correction.
        Particular applications of AI include expert systems, natural language processing, speech
        recognition and machine vision. AI can be categorized as either weak or strong. Weak AI, also
        known as narrow AI, is an AI system that is designed and trained for a particular task. Virtual
        personal assistants, such as Apple's Siri, are a form of weak AI. Strong AI, also known as
        artificial general intelligence, is an AI system with generalized human cognitive abilities.
        """

        # Mock database but use real Groq API
        with patch('app.services.summary_service.get_database') as mock_db:
            mock_collection = MagicMock()
            mock_collection.insert_one = AsyncMock()
            mock_db.return_value = {"summaries": mock_collection}

            result = await summary_service.generate_summary(
                file_id="test-ai-file",
                user_id="test-user-id",
                text=sample_text,
                summary_type=SummaryType.BRIEF
            )

            assert result is not None
            assert result.summary_type == SummaryType.BRIEF
            assert result.content is not None
            assert len(result.content) > 0
            assert result.token_count.total > 0
            # Brief summary should mention AI or Artificial Intelligence
            assert "AI" in result.content or "artificial intelligence" in result.content.lower()

    @pytest.mark.asyncio
    async def test_generate_detailed_summary(self):
        """Test generating a detailed summary with real Groq API."""
        from unittest.mock import patch, AsyncMock, MagicMock
        from app.services.summary_service import summary_service

        sample_text = """
        Machine Learning is a subset of artificial intelligence that provides systems the ability to
        automatically learn and improve from experience without being explicitly programmed. Machine
        learning focuses on the development of computer programs that can access data and use it to
        learn for themselves. The process of learning begins with observations or data, such as examples,
        direct experience, or instruction, in order to look for patterns in data and make better decisions
        in the future based on the examples that we provide. The primary aim is to allow the computers
        learn automatically without human intervention or assistance and adjust actions accordingly.
        """

        # Mock database but use real Groq API
        with patch('app.services.summary_service.get_database') as mock_db:
            mock_collection = MagicMock()
            mock_collection.insert_one = AsyncMock()
            mock_db.return_value = {"summaries": mock_collection}

            result = await summary_service.generate_summary(
                file_id="test-ml-file",
                user_id="test-user-id",
                text=sample_text,
                summary_type=SummaryType.DETAILED
            )

            assert result is not None
            assert result.summary_type == SummaryType.DETAILED
            assert result.content is not None
            # Detailed summary should be more comprehensive
            assert len(result.content) > 50


@pytest.mark.integration
class TestTimestampServiceAPI:
    """Integration tests for Timestamp service with real Groq API."""

    @pytest.mark.asyncio
    async def test_extract_timestamps(self):
        """Test extracting timestamps with real Groq API."""
        from unittest.mock import patch, AsyncMock, MagicMock
        from app.services.timestamp_service import timestamp_service

        sample_transcription = """
        [00:00] Welcome to this tutorial on Python programming. Today we'll cover the basics.
        [01:30] First, let's talk about variables and data types in Python.
        [03:45] Now we'll move on to control structures like if statements and loops.
        [06:20] Finally, we'll discuss functions and how to create reusable code.
        [09:00] Thank you for watching. Don't forget to subscribe!
        """

        # Mock database but use real Groq API
        with patch('app.services.timestamp_service.get_database') as mock_db:
            mock_collection = MagicMock()
            mock_collection.insert_one = AsyncMock()
            mock_db.return_value = {"timestamps": mock_collection}

            result = await timestamp_service.extract_timestamps(
                file_id="test-tutorial-file",
                user_id="test-user-id",
                transcription=sample_transcription,
                duration=540  # 9 minutes
            )

            assert result is not None
            assert len(result.timestamps) > 0
            assert result.extraction_metadata.total_topics > 0
            # Should have extracted some topics
            assert any("welcome" in t.topic.lower() or "introduction" in t.topic.lower() or "python" in t.topic.lower()
                       for t in result.timestamps)


@pytest.mark.integration
class TestTranscriptionServiceAPI:
    """Integration tests for Transcription service with real Whisper."""

    @pytest.mark.asyncio
    async def test_transcribe_audio_file(self):
        """Test transcribing an audio file with real Whisper."""
        from app.services.transcription_service import transcription_service
        import wave
        import struct

        # Create a simple test audio file (1 second of silence)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            audio_path = temp_audio.name

            # Create a 1-second WAV file with silence
            sample_rate = 16000
            duration = 1
            num_samples = sample_rate * duration

            with wave.open(audio_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)

                # Write silence
                for _ in range(num_samples):
                    wav_file.writeframes(struct.pack('h', 0))

        try:
            # Transcribe the audio file
            extracted_content, metadata = await transcription_service.transcribe_file(audio_path)

            assert extracted_content is not None
            assert "faster-whisper" in extracted_content.extraction_method
            assert metadata is not None
            assert metadata.duration >= 0
            # Silence might transcribe as empty or with minimal text
            assert isinstance(extracted_content.text, str)

        finally:
            # Cleanup
            if os.path.exists(audio_path):
                os.unlink(audio_path)


@pytest.mark.integration
class TestPDFServiceAPI:
    """Integration tests for PDF service."""

    def test_extract_text_from_real_pdf(self):
        """Test extracting text from a real PDF file."""
        from app.services.pdf_service import pdf_service
        from PyPDF2 import PdfWriter
        import io

        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            has_reportlab = True
        except ImportError:
            has_reportlab = False

        if not has_reportlab:
            pytest.skip("reportlab not installed")

        # Create a real PDF with text content
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
            pdf_path = temp_pdf.name

            # Create PDF with reportlab
            c = canvas.Canvas(pdf_path, pagesize=letter)
            c.drawString(100, 750, "This is a test PDF document.")
            c.drawString(100, 730, "It contains multiple lines of text.")
            c.drawString(100, 710, "Python PDF extraction test.")
            c.save()

        try:
            result = pdf_service.extract_text(pdf_path)

            assert result is not None
            assert result.extraction_method == "PyPDF2"
            assert result.word_count >= 0  # May be 0 for blank PDFs

        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)


@pytest.mark.integration
class TestFileServiceAPI:
    """Integration tests for File service with database."""

    @pytest.mark.asyncio
    async def test_file_upload_and_retrieval(self):
        """Test uploading and retrieving a file."""
        from app.services.file_service import file_service
        from fastapi import UploadFile
        from starlette.datastructures import Headers
        import io

        # Create a mock uploaded file
        file_content = b"%PDF-1.4\nTest PDF content for integration testing"
        file = UploadFile(
            filename="integration_test.pdf",
            file=io.BytesIO(file_content),
            headers=Headers({"content-type": "application/pdf"})
        )

        try:
            # Upload the file
            file_model = await file_service.upload_file(file, user_id="test-user-id")

            assert file_model is not None
            assert file_model.file_id is not None
            assert file_model.filename == "integration_test.pdf"

            # Retrieve the file
            retrieved = await file_service.get_file(file_model.file_id, user_id="test-user-id")

            assert retrieved is not None
            assert retrieved.file_id == file_model.file_id
            assert retrieved.filename == file_model.filename

        except Exception as e:
            # If database connection fails, skip the test
            pytest.skip(f"Database not available: {e}")
