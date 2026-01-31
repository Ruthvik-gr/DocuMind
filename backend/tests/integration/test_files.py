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

        with patch('app.api.v1.endpoints.files.file_service.list_files', new_callable=AsyncMock) as mock_list:
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
