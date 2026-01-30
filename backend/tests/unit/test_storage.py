"""
Unit tests for file storage module.
"""
import pytest
import io
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.core.constants import FileType


class TestFileStorage:
    """Test FileStorage class."""

    @pytest.fixture
    def temp_storage_path(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_ensure_directories(self, temp_storage_path):
        """Test that storage directories are created."""
        with patch('app.core.storage.settings') as mock_settings:
            mock_settings.STORAGE_PATH = temp_storage_path

            from app.core.storage import FileStorage
            storage = FileStorage()

            # Check directories exist
            assert (Path(temp_storage_path) / "pdfs").exists()
            assert (Path(temp_storage_path) / "audios").exists()
            assert (Path(temp_storage_path) / "videos").exists()
            assert (Path(temp_storage_path) / "extracted").exists()

    def test_save_file_pdf(self, temp_storage_path):
        """Test saving a PDF file."""
        with patch('app.core.storage.settings') as mock_settings:
            mock_settings.STORAGE_PATH = temp_storage_path

            from app.core.storage import FileStorage
            storage = FileStorage()

            content = b"PDF content"
            file = io.BytesIO(content)

            file_id, file_path = storage.save_file(file, "test.pdf", FileType.PDF)

            assert file_id is not None
            assert os.path.exists(file_path)
            assert file_path.endswith(".pdf")

            with open(file_path, "rb") as f:
                assert f.read() == content

    def test_save_file_audio(self, temp_storage_path):
        """Test saving an audio file."""
        with patch('app.core.storage.settings') as mock_settings:
            mock_settings.STORAGE_PATH = temp_storage_path

            from app.core.storage import FileStorage
            storage = FileStorage()

            content = b"Audio content"
            file = io.BytesIO(content)

            file_id, file_path = storage.save_file(file, "test.mp3", FileType.AUDIO)

            assert file_id is not None
            assert "audios" in file_path
            assert os.path.exists(file_path)

    def test_save_file_video(self, temp_storage_path):
        """Test saving a video file."""
        with patch('app.core.storage.settings') as mock_settings:
            mock_settings.STORAGE_PATH = temp_storage_path

            from app.core.storage import FileStorage
            storage = FileStorage()

            content = b"Video content"
            file = io.BytesIO(content)

            file_id, file_path = storage.save_file(file, "test.mp4", FileType.VIDEO)

            assert file_id is not None
            assert "videos" in file_path
            assert os.path.exists(file_path)

    def test_get_file_path(self, temp_storage_path):
        """Test getting file path."""
        with patch('app.core.storage.settings') as mock_settings:
            mock_settings.STORAGE_PATH = temp_storage_path

            from app.core.storage import FileStorage
            storage = FileStorage()

            file_path = storage.get_file_path("test-id", FileType.PDF, ".pdf")

            assert "test-id.pdf" in str(file_path)
            assert "pdfs" in str(file_path)

    def test_delete_file_existing(self, temp_storage_path):
        """Test deleting an existing file."""
        with patch('app.core.storage.settings') as mock_settings:
            mock_settings.STORAGE_PATH = temp_storage_path

            from app.core.storage import FileStorage
            storage = FileStorage()

            # Create a test file
            test_file = Path(temp_storage_path) / "test.txt"
            test_file.write_text("content")

            assert test_file.exists()

            storage.delete_file(str(test_file))

            assert not test_file.exists()

    def test_delete_file_non_existing(self, temp_storage_path):
        """Test deleting a non-existent file (should not raise)."""
        with patch('app.core.storage.settings') as mock_settings:
            mock_settings.STORAGE_PATH = temp_storage_path

            from app.core.storage import FileStorage
            storage = FileStorage()

            # Should not raise exception
            storage.delete_file("/non/existent/path.txt")
