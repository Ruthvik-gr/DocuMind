"""
Unit tests for text processing utilities.
"""
import pytest
from app.utils.text_processors import count_words, clean_text, truncate_text


class TestTextProcessors:
    """Test text processing functions."""

    def test_count_words_simple(self):
        """Test word counting with simple text."""
        text = "This is a test"
        assert count_words(text) == 4

    def test_count_words_empty(self):
        """Test word counting with empty string."""
        assert count_words("") == 0
        assert count_words("   ") == 0

    def test_count_words_multiple_spaces(self):
        """Test word counting with multiple spaces."""
        text = "This  is   a    test"
        assert count_words(text) == 4

    def test_clean_text(self):
        """Test text cleaning."""
        text = "This  is   a\n\ntest   with   spaces"
        cleaned = clean_text(text)
        assert "  " not in cleaned
        assert "\n\n" not in cleaned

    def test_clean_text_empty(self):
        """Test cleaning empty string."""
        assert clean_text("") == ""

    def test_truncate_text_short(self):
        """Test truncating text shorter than max length."""
        text = "Short text"
        assert truncate_text(text, max_length=50) == text

    def test_truncate_text_long(self):
        """Test truncating long text."""
        text = "A" * 1000
        truncated = truncate_text(text, max_length=100)
        assert len(truncated) == 103  # 100 + "..."
        assert truncated.endswith("...")
