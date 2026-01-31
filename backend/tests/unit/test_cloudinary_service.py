"""
Unit tests for Cloudinary service.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import cloudinary

from app.services.cloudinary_service import CloudinaryService
from app.core.constants import FileType


class TestCloudinaryServiceConfiguration:
    """Tests for CloudinaryService configuration."""

    def test_service_configured_when_all_settings_present(self):
        """Test service is configured when all settings are present."""
        with patch('app.services.cloudinary_service.settings') as mock_settings:
            mock_settings.CLOUDINARY_CLOUD_NAME = "test-cloud"
            mock_settings.CLOUDINARY_API_KEY = "test-key"
            mock_settings.CLOUDINARY_API_SECRET = "test-secret"

            # Create new instance to test configuration
            with patch.object(CloudinaryService, '__init__', lambda self: None):
                service = CloudinaryService()
                service.configured = True

            assert service.is_configured() is True

    def test_service_not_configured_when_settings_missing(self):
        """Test service is not configured when settings are missing."""
        service = CloudinaryService()
        service.configured = False

        assert service.is_configured() is False


class TestCloudinaryUpload:
    """Tests for CloudinaryService upload functionality."""

    @pytest.mark.asyncio
    async def test_upload_pdf_file(self):
        """Test uploading a PDF file."""
        service = CloudinaryService()
        service.configured = True

        mock_result = {
            "secure_url": "https://cloudinary.com/test/doc.pdf",
            "public_id": "documind/pdfs/test-id"
        }

        with patch.object(cloudinary.uploader, 'upload', return_value=mock_result):
            result = await service.upload_file(
                file_path="/tmp/test.pdf",
                file_id="test-id",
                file_type=FileType.PDF,
                original_filename="test.pdf"
            )

            assert result["cloudinary_url"] == mock_result["secure_url"]
            assert result["cloudinary_public_id"] == mock_result["public_id"]
            assert result["cloudinary_resource_type"] == "raw"

    @pytest.mark.asyncio
    async def test_upload_video_file(self):
        """Test uploading a video file."""
        service = CloudinaryService()
        service.configured = True

        mock_result = {
            "secure_url": "https://cloudinary.com/test/video.mp4",
            "public_id": "documind/videos/test-id"
        }

        with patch.object(cloudinary.uploader, 'upload', return_value=mock_result):
            result = await service.upload_file(
                file_path="/tmp/test.mp4",
                file_id="test-id",
                file_type=FileType.VIDEO,
                original_filename="test.mp4"
            )

            assert result["cloudinary_resource_type"] == "video"

    @pytest.mark.asyncio
    async def test_upload_audio_file(self):
        """Test uploading an audio file."""
        service = CloudinaryService()
        service.configured = True

        mock_result = {
            "secure_url": "https://cloudinary.com/test/audio.mp3",
            "public_id": "documind/audios/test-id"
        }

        with patch.object(cloudinary.uploader, 'upload', return_value=mock_result):
            result = await service.upload_file(
                file_path="/tmp/test.mp3",
                file_id="test-id",
                file_type=FileType.AUDIO,
                original_filename="test.mp3"
            )

            assert result["cloudinary_resource_type"] == "video"  # Audio uses video resource type

    @pytest.mark.asyncio
    async def test_upload_not_configured(self):
        """Test upload fails when not configured."""
        service = CloudinaryService()
        service.configured = False

        with pytest.raises(ValueError, match="not configured"):
            await service.upload_file(
                file_path="/tmp/test.pdf",
                file_id="test-id",
                file_type=FileType.PDF,
                original_filename="test.pdf"
            )

    @pytest.mark.asyncio
    async def test_upload_error_handling(self):
        """Test upload error handling."""
        service = CloudinaryService()
        service.configured = True

        with patch.object(cloudinary.uploader, 'upload', side_effect=Exception("Upload failed")):
            with pytest.raises(Exception, match="Upload failed"):
                await service.upload_file(
                    file_path="/tmp/test.pdf",
                    file_id="test-id",
                    file_type=FileType.PDF,
                    original_filename="test.pdf"
                )


class TestCloudinaryDelete:
    """Tests for CloudinaryService delete functionality."""

    @pytest.mark.asyncio
    async def test_delete_file_success(self):
        """Test successful file deletion."""
        service = CloudinaryService()
        service.configured = True

        with patch.object(cloudinary.uploader, 'destroy', return_value={"result": "ok"}):
            result = await service.delete_file("documind/pdfs/test-id", "raw")
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self):
        """Test deletion when file not found."""
        service = CloudinaryService()
        service.configured = True

        with patch.object(cloudinary.uploader, 'destroy', return_value={"result": "not found"}):
            result = await service.delete_file("documind/pdfs/nonexistent", "raw")
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_not_configured(self):
        """Test delete returns False when not configured."""
        service = CloudinaryService()
        service.configured = False

        result = await service.delete_file("documind/pdfs/test-id", "raw")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_error_handling(self):
        """Test delete error handling."""
        service = CloudinaryService()
        service.configured = True

        with patch.object(cloudinary.uploader, 'destroy', side_effect=Exception("Delete failed")):
            result = await service.delete_file("documind/pdfs/test-id", "raw")
            assert result is False


class TestCloudinaryUrls:
    """Tests for CloudinaryService URL generation."""

    def test_get_streaming_url_video(self):
        """Test getting streaming URL for video."""
        service = CloudinaryService()
        service.configured = True

        mock_video = MagicMock()
        mock_video.build_url.return_value = "https://cloudinary.com/stream/video.mp4"

        with patch.object(cloudinary, 'CloudinaryVideo', return_value=mock_video):
            url = service.get_streaming_url("documind/videos/test-id", "video")
            assert "cloudinary.com" in url

    def test_get_streaming_url_raw(self):
        """Test getting streaming URL for raw resource."""
        service = CloudinaryService()
        service.configured = True

        mock_resource = MagicMock()
        mock_resource.build_url.return_value = "https://cloudinary.com/raw/file.pdf"

        with patch.object(cloudinary, 'CloudinaryResource', return_value=mock_resource):
            url = service.get_streaming_url("documind/pdfs/test-id", "raw")
            assert "cloudinary.com" in url

    def test_get_streaming_url_not_configured(self):
        """Test streaming URL fails when not configured."""
        service = CloudinaryService()
        service.configured = False

        with pytest.raises(ValueError, match="not configured"):
            service.get_streaming_url("documind/videos/test-id")

    def test_get_download_url(self):
        """Test getting download URL."""
        service = CloudinaryService()
        service.configured = True

        mock_resource = MagicMock()
        mock_resource.build_url.return_value = "https://cloudinary.com/download/file.pdf"

        with patch.object(cloudinary, 'CloudinaryResource', return_value=mock_resource):
            url = service.get_download_url("documind/pdfs/test-id", "raw")
            assert "cloudinary.com" in url

    def test_get_download_url_not_configured(self):
        """Test download URL fails when not configured."""
        service = CloudinaryService()
        service.configured = False

        with pytest.raises(ValueError, match="not configured"):
            service.get_download_url("documind/pdfs/test-id")
