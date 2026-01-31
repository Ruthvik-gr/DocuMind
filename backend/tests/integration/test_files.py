"""
Integration tests for file endpoints.
"""
import pytest
import io
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.mark.integration
class TestFileEndpoints:
    """Test file-related endpoints."""

    def test_upload_file_pdf(self, test_client):
        """Test uploading a PDF file."""
        with patch('app.api.v1.endpoints.files.file_service.upload_file', new_callable=AsyncMock) as mock_upload, \
             patch('app.api.v1.endpoints.files.process_file_background', new_callable=AsyncMock):
            mock_file_model = MagicMock()
            mock_file_model.file_id = "test-file-id"
            mock_file_model.filename = "test.pdf"
            mock_file_model.file_type = "pdf"
            mock_file_model.file_size = 1024
            mock_file_model.processing_status = "pending"
            mock_file_model.upload_date = "2024-01-01T00:00:00"
            mock_file_model.file_path = "/path/to/test.pdf"
            mock_upload.return_value = mock_file_model

            files = {"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 test content"), "application/pdf")}
            response = test_client.post("/api/v1/files/upload", files=files)

            assert response.status_code == 200
            data = response.json()
            assert data["file_id"] == "test-file-id"
            assert data["filename"] == "test.pdf"

    def test_upload_file_invalid_type(self, test_client):
        """Test uploading an invalid file type."""
        from app.utils.exceptions import InvalidFileError

        with patch('app.services.file_service.file_service.upload_file', new_callable=AsyncMock) as mock_upload:
            mock_upload.side_effect = InvalidFileError("Invalid file type")

            files = {"file": ("test.txt", io.BytesIO(b"text content"), "text/plain")}
            response = test_client.post("/api/v1/files/upload", files=files)

            assert response.status_code == 400

    def test_upload_file_server_error(self, test_client):
        """Test server error during file upload."""
        with patch('app.services.file_service.file_service.upload_file', new_callable=AsyncMock) as mock_upload:
            mock_upload.side_effect = Exception("Server error")

            files = {"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")}
            response = test_client.post("/api/v1/files/upload", files=files)

            assert response.status_code == 500

    def test_get_file_success(self, test_client):
        """Test getting file details."""
        from datetime import datetime
        from app.models.file import FileModel, ExtractedContent

        with patch('app.services.file_service.file_service.get_file', new_callable=AsyncMock) as mock_get:
            mock_file = MagicMock(spec=FileModel)
            mock_file.file_id = "test-id"
            mock_file.filename = "test.pdf"
            mock_file.file_type = "pdf"
            mock_file.file_size = 1024
            mock_file.mime_type = "application/pdf"
            mock_file.processing_status = "completed"
            mock_file.processing_error = None
            mock_file.upload_date = datetime.utcnow()
            mock_file.created_at = datetime.utcnow()
            mock_file.updated_at = datetime.utcnow()

            mock_content = MagicMock()
            mock_content.model_dump.return_value = {
                "text": "Extracted text",
                "word_count": 2,
                "language": "en",
                "extraction_method": "PyPDF2"
            }
            mock_file.extracted_content = mock_content
            mock_file.metadata = None

            mock_get.return_value = mock_file

            response = test_client.get("/api/v1/files/test-id")

            assert response.status_code == 200
            data = response.json()
            assert data["file_id"] == "test-id"
            assert data["extracted_content"]["text"] == "Extracted text"

    def test_get_file_not_found(self, test_client):
        """Test getting a non-existent file."""
        from app.utils.exceptions import FileNotFoundError

        with patch('app.services.file_service.file_service.get_file', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = FileNotFoundError("File not found")

            response = test_client.get("/api/v1/files/non-existent-id")

            assert response.status_code == 404

    def test_get_file_server_error(self, test_client):
        """Test server error when getting file."""
        with patch('app.services.file_service.file_service.get_file', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Database error")

            response = test_client.get("/api/v1/files/test-id")

            assert response.status_code == 500

    def test_stream_file_no_auth(self, test_client):
        """Test streaming file without authentication returns 401."""
        # The stream endpoint requires token in query param or header
        # Since it doesn't use get_current_user dependency, it checks token directly
        response = test_client.get("/api/v1/files/test-id/stream")
        assert response.status_code == 401

    def test_stream_file_with_cloudinary_url(self, test_client):
        """Test streaming file redirects to Cloudinary URL."""
        with patch('app.api.v1.endpoints.files.decode_token') as mock_decode, \
             patch('app.api.v1.endpoints.files.file_service.get_file', new_callable=AsyncMock) as mock_get:
            mock_decode.return_value = {"sub": "user-id", "type": "access"}

            mock_file = MagicMock()
            mock_file.cloudinary_url = "https://res.cloudinary.com/test/video.mp4"
            mock_get.return_value = mock_file

            response = test_client.get(
                "/api/v1/files/test-id/stream?token=valid-token",
                follow_redirects=False
            )

            assert response.status_code == 307  # Redirect
            assert response.headers["location"] == "https://res.cloudinary.com/test/video.mp4"

    def test_stream_file_no_cloudinary_url(self, test_client):
        """Test streaming file without Cloudinary URL returns 404."""
        with patch('app.api.v1.endpoints.files.decode_token') as mock_decode, \
             patch('app.api.v1.endpoints.files.file_service.get_file', new_callable=AsyncMock) as mock_get:
            mock_decode.return_value = {"sub": "user-id", "type": "access"}

            mock_file = MagicMock()
            mock_file.cloudinary_url = None
            mock_get.return_value = mock_file

            response = test_client.get("/api/v1/files/test-id/stream?token=valid-token")

            assert response.status_code == 404

    def test_stream_file_invalid_token(self, test_client):
        """Test streaming file with invalid token returns 401."""
        with patch('app.api.v1.endpoints.files.decode_token') as mock_decode:
            mock_decode.return_value = None

            response = test_client.get("/api/v1/files/test-id/stream?token=invalid-token")

            assert response.status_code == 401

    def test_stream_file_not_found(self, test_client):
        """Test streaming a non-existent file."""
        from app.utils.exceptions import FileNotFoundError

        with patch('app.api.v1.endpoints.files.decode_token') as mock_decode, \
             patch('app.api.v1.endpoints.files.file_service.get_file', new_callable=AsyncMock) as mock_get:
            mock_decode.return_value = {"sub": "user-id", "type": "access"}
            mock_get.side_effect = FileNotFoundError("File not found")

            response = test_client.get("/api/v1/files/test-id/stream?token=valid-token")

            assert response.status_code == 404

    def test_stream_file_server_error(self, test_client):
        """Test server error when streaming file."""
        with patch('app.api.v1.endpoints.files.decode_token') as mock_decode, \
             patch('app.api.v1.endpoints.files.file_service.get_file', new_callable=AsyncMock) as mock_get:
            mock_decode.return_value = {"sub": "user-id", "type": "access"}
            mock_get.side_effect = Exception("Unexpected error")

            response = test_client.get("/api/v1/files/test-id/stream?token=valid-token")

            assert response.status_code == 500

    def test_list_files(self, test_client, mock_db):
        """Test listing user's files."""
        from datetime import datetime

        with patch('app.api.v1.endpoints.files.file_service.list_files', new_callable=AsyncMock) as mock_list, \
             patch('app.api.v1.endpoints.files.get_database') as mock_get_db:
            mock_file1 = MagicMock()
            mock_file1.file_id = "file-1"
            mock_file1.filename = "test1.pdf"
            mock_file1.file_type = "pdf"
            mock_file1.file_size = 1024
            mock_file1.processing_status = "completed"
            mock_file1.created_at = datetime.utcnow()

            mock_file2 = MagicMock()
            mock_file2.file_id = "file-2"
            mock_file2.filename = "test2.mp4"
            mock_file2.file_type = "video"
            mock_file2.file_size = 2048
            mock_file2.processing_status = "completed"
            mock_file2.created_at = datetime.utcnow()

            mock_list.return_value = [mock_file1, mock_file2]

            # Mock database for chat history check
            mock_collection = MagicMock()
            mock_collection.find_one = AsyncMock(return_value=None)
            mock_get_db.return_value = {"chat_history": mock_collection}

            response = test_client.get("/api/v1/files/")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert len(data["files"]) == 2

    def test_delete_file_success(self, test_client):
        """Test deleting a file."""
        with patch('app.api.v1.endpoints.files.file_service.delete_file', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True

            response = test_client.delete("/api/v1/files/test-id")

            assert response.status_code == 200
            assert response.json()["message"] == "File deleted successfully"

    def test_delete_file_not_found(self, test_client):
        """Test deleting a non-existent file."""
        from app.utils.exceptions import FileNotFoundError

        with patch('app.api.v1.endpoints.files.file_service.delete_file', new_callable=AsyncMock) as mock_delete:
            mock_delete.side_effect = FileNotFoundError("File not found")

            response = test_client.delete("/api/v1/files/non-existent-id")

            assert response.status_code == 404

    def test_delete_file_server_error(self, test_client):
        """Test server error when deleting file."""
        with patch('app.api.v1.endpoints.files.file_service.delete_file', new_callable=AsyncMock) as mock_delete:
            mock_delete.side_effect = Exception("Database error")

            response = test_client.delete("/api/v1/files/test-id")

            assert response.status_code == 500

    def test_list_files_error(self, test_client):
        """Test error when listing files."""
        with patch('app.api.v1.endpoints.files.file_service.list_files', new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("Database error")

            response = test_client.get("/api/v1/files/")

            assert response.status_code == 500

    def test_get_file_with_metadata(self, test_client):
        """Test getting file with metadata."""
        from datetime import datetime

        with patch('app.services.file_service.file_service.get_file', new_callable=AsyncMock) as mock_get:
            mock_file = MagicMock()
            mock_file.file_id = "test-id"
            mock_file.filename = "test.mp4"
            mock_file.file_type = "video"
            mock_file.file_size = 10240
            mock_file.mime_type = "video/mp4"
            mock_file.processing_status = "completed"
            mock_file.processing_error = None
            mock_file.upload_date = datetime.utcnow()
            mock_file.created_at = datetime.utcnow()
            mock_file.updated_at = datetime.utcnow()

            mock_content = MagicMock()
            mock_content.model_dump.return_value = {
                "text": "Transcribed text",
                "word_count": 10,
                "language": "en",
                "extraction_method": "Whisper"
            }
            mock_file.extracted_content = mock_content

            mock_metadata = MagicMock()
            mock_metadata.model_dump.return_value = {
                "duration": 120,
                "format": "mp4",
                "resolution": "1920x1080"
            }
            mock_file.metadata = mock_metadata

            mock_get.return_value = mock_file

            response = test_client.get("/api/v1/files/test-id")

            assert response.status_code == 200
            data = response.json()
            assert data["metadata"]["duration"] == 120

    def test_stream_file_with_header_auth(self, test_client):
        """Test streaming file with Bearer token in header."""
        with patch('app.api.v1.endpoints.files.decode_token') as mock_decode, \
             patch('app.api.v1.endpoints.files.file_service.get_file', new_callable=AsyncMock) as mock_get:
            mock_decode.return_value = {"sub": "user-id", "type": "access"}

            mock_file = MagicMock()
            mock_file.cloudinary_url = "https://res.cloudinary.com/test/video.mp4"
            mock_get.return_value = mock_file

            response = test_client.get(
                "/api/v1/files/test-id/stream",
                headers={"Authorization": "Bearer valid-token"},
                follow_redirects=False
            )

            assert response.status_code == 307

    def test_stream_file_wrong_token_type(self, test_client):
        """Test streaming file with wrong token type (refresh instead of access)."""
        with patch('app.api.v1.endpoints.files.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": "user-id", "type": "refresh"}

            response = test_client.get("/api/v1/files/test-id/stream?token=refresh-token")

            assert response.status_code == 401

    def test_stream_file_token_without_sub(self, test_client):
        """Test streaming file with token that has no subject."""
        with patch('app.api.v1.endpoints.files.decode_token') as mock_decode:
            mock_decode.return_value = {"type": "access"}  # No "sub" field

            response = test_client.get("/api/v1/files/test-id/stream?token=incomplete-token")

            assert response.status_code == 401


@pytest.mark.integration
class TestProcessFileBackground:
    """Tests for the background file processing function."""

    @pytest.mark.asyncio
    async def test_process_pdf_file(self):
        """Test processing a PDF file in background."""
        from app.api.v1.endpoints.files import process_file_background
        from app.core.constants import FileType
        from app.models.file import ExtractedContent

        with patch('app.api.v1.endpoints.files.file_service.update_processing_status', new_callable=AsyncMock) as mock_status, \
             patch('app.api.v1.endpoints.files.pdf_service.extract_text') as mock_extract, \
             patch('app.api.v1.endpoints.files.file_service.update_extracted_content', new_callable=AsyncMock) as mock_content, \
             patch('app.api.v1.endpoints.files.langchain_service.create_vector_store', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.files.cloudinary_service.is_configured', return_value=True), \
             patch('app.api.v1.endpoints.files.cloudinary_service.upload_file', new_callable=AsyncMock) as mock_upload, \
             patch('app.api.v1.endpoints.files.file_service.update_cloudinary_info', new_callable=AsyncMock), \
             patch('app.core.storage.file_storage') as mock_storage:

            mock_extract.return_value = ExtractedContent(
                text="PDF content",
                word_count=2,
                language="en",
                extraction_method="PyPDF2"
            )
            mock_upload.return_value = {
                "cloudinary_url": "https://cloudinary.com/test.pdf",
                "cloudinary_public_id": "test-id"
            }
            mock_storage.delete_file = MagicMock()

            await process_file_background("file-id", "/path/to/file.pdf", FileType.PDF, "file.pdf")

            assert mock_status.call_count == 2  # PROCESSING and COMPLETED
            mock_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_video_file(self):
        """Test processing a video file in background."""
        from app.api.v1.endpoints.files import process_file_background
        from app.core.constants import FileType
        from app.models.file import ExtractedContent, FileMetadata

        with patch('app.api.v1.endpoints.files.file_service.update_processing_status', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.files.transcription_service.transcribe_file', new_callable=AsyncMock) as mock_transcribe, \
             patch('app.api.v1.endpoints.files.file_service.update_extracted_content', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.files.file_service.update_metadata', new_callable=AsyncMock) as mock_meta, \
             patch('app.api.v1.endpoints.files.langchain_service.create_vector_store', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.files.cloudinary_service.is_configured', return_value=True), \
             patch('app.api.v1.endpoints.files.cloudinary_service.upload_file', new_callable=AsyncMock) as mock_upload, \
             patch('app.api.v1.endpoints.files.file_service.update_cloudinary_info', new_callable=AsyncMock), \
             patch('app.core.storage.file_storage') as mock_storage:

            mock_content = ExtractedContent(
                text="Transcribed video",
                word_count=2,
                language="en",
                extraction_method="Whisper"
            )
            mock_metadata = FileMetadata(duration=120, format="mp4")
            mock_transcribe.return_value = (mock_content, mock_metadata)

            mock_upload.return_value = {"cloudinary_url": "url", "cloudinary_public_id": "id"}
            mock_storage.delete_file = MagicMock()

            await process_file_background("file-id", "/path/to/file.mp4", FileType.VIDEO, "file.mp4")

            mock_meta.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_audio_file(self):
        """Test processing an audio file in background."""
        from app.api.v1.endpoints.files import process_file_background
        from app.core.constants import FileType
        from app.models.file import ExtractedContent, FileMetadata

        with patch('app.api.v1.endpoints.files.file_service.update_processing_status', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.files.transcription_service.transcribe_file', new_callable=AsyncMock) as mock_transcribe, \
             patch('app.api.v1.endpoints.files.file_service.update_extracted_content', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.files.file_service.update_metadata', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.files.langchain_service.create_vector_store', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.files.cloudinary_service.is_configured', return_value=True), \
             patch('app.api.v1.endpoints.files.cloudinary_service.upload_file', new_callable=AsyncMock) as mock_upload, \
             patch('app.api.v1.endpoints.files.file_service.update_cloudinary_info', new_callable=AsyncMock), \
             patch('app.core.storage.file_storage') as mock_storage:

            mock_content = ExtractedContent(
                text="Transcribed audio",
                word_count=2,
                language="en",
                extraction_method="Whisper"
            )
            mock_metadata = FileMetadata(duration=60, format="mp3", sample_rate=44100)
            mock_transcribe.return_value = (mock_content, mock_metadata)

            mock_upload.return_value = {"cloudinary_url": "url", "cloudinary_public_id": "id"}
            mock_storage.delete_file = MagicMock()

            await process_file_background("file-id", "/path/to/file.mp3", FileType.AUDIO, "file.mp3")

            mock_transcribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_file_cloudinary_not_configured(self):
        """Test processing file when Cloudinary is not configured."""
        from app.api.v1.endpoints.files import process_file_background
        from app.core.constants import FileType, ProcessingStatus
        from app.models.file import ExtractedContent

        with patch('app.api.v1.endpoints.files.file_service.update_processing_status', new_callable=AsyncMock) as mock_status, \
             patch('app.api.v1.endpoints.files.pdf_service.extract_text') as mock_extract, \
             patch('app.api.v1.endpoints.files.file_service.update_extracted_content', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.files.langchain_service.create_vector_store', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.files.cloudinary_service.is_configured', return_value=False):

            mock_extract.return_value = ExtractedContent(
                text="PDF content",
                word_count=2,
                language="en",
                extraction_method="PyPDF2"
            )

            await process_file_background("file-id", "/path/to/file.pdf", FileType.PDF, "file.pdf")

            # Should fail due to Cloudinary not configured
            last_call = mock_status.call_args_list[-1]
            assert last_call[0][1] == ProcessingStatus.FAILED

    @pytest.mark.asyncio
    async def test_process_file_cloudinary_upload_fails(self):
        """Test processing file when Cloudinary upload fails."""
        from app.api.v1.endpoints.files import process_file_background
        from app.core.constants import FileType, ProcessingStatus
        from app.models.file import ExtractedContent

        with patch('app.api.v1.endpoints.files.file_service.update_processing_status', new_callable=AsyncMock) as mock_status, \
             patch('app.api.v1.endpoints.files.pdf_service.extract_text') as mock_extract, \
             patch('app.api.v1.endpoints.files.file_service.update_extracted_content', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.files.langchain_service.create_vector_store', new_callable=AsyncMock), \
             patch('app.api.v1.endpoints.files.cloudinary_service.is_configured', return_value=True), \
             patch('app.api.v1.endpoints.files.cloudinary_service.upload_file', new_callable=AsyncMock) as mock_upload:

            mock_extract.return_value = ExtractedContent(
                text="PDF content",
                word_count=2,
                language="en",
                extraction_method="PyPDF2"
            )
            mock_upload.side_effect = Exception("Cloudinary upload failed")

            await process_file_background("file-id", "/path/to/file.pdf", FileType.PDF, "file.pdf")

            # Should fail
            last_call = mock_status.call_args_list[-1]
            assert last_call[0][1] == ProcessingStatus.FAILED

    @pytest.mark.asyncio
    async def test_process_file_general_error(self):
        """Test processing file with general error."""
        from app.api.v1.endpoints.files import process_file_background
        from app.core.constants import FileType, ProcessingStatus

        with patch('app.api.v1.endpoints.files.file_service.update_processing_status', new_callable=AsyncMock) as mock_status, \
             patch('app.api.v1.endpoints.files.pdf_service.extract_text') as mock_extract:

            mock_extract.side_effect = Exception("PDF extraction failed")

            await process_file_background("file-id", "/path/to/file.pdf", FileType.PDF, "file.pdf")

            # Should fail with FAILED status
            last_call = mock_status.call_args_list[-1]
            assert last_call[0][1] == ProcessingStatus.FAILED
            assert "error" in last_call[1]
