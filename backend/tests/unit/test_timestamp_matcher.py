"""
Unit tests for timestamp_matcher utility.
"""
import pytest
from app.utils.timestamp_matcher import (
    extract_keywords,
    calculate_similarity,
    find_relevant_timestamp,
    find_relevant_timestamps
)


class TestExtractKeywords:
    """Tests for extract_keywords function."""

    def test_extract_basic_keywords(self):
        """Test extraction of basic keywords."""
        text = "Introduction to machine learning and neural networks"
        keywords = extract_keywords(text)

        assert "introduction" in keywords
        assert "machine" in keywords
        assert "learning" in keywords
        assert "neural" in keywords
        assert "networks" in keywords

    def test_stop_words_removed(self):
        """Test that stop words are filtered out."""
        text = "The quick brown fox jumps over the lazy dog"
        keywords = extract_keywords(text)

        assert "the" not in keywords
        assert "over" not in keywords
        assert "quick" in keywords
        assert "brown" in keywords
        assert "jumps" in keywords

    def test_short_words_filtered(self):
        """Test that words shorter than 3 characters are filtered."""
        text = "I am a big fan of AI and ML"
        keywords = extract_keywords(text)

        # 'I', 'am', 'a', 'of', 'AI', 'ML' should be filtered (< 3 chars or stop words)
        assert "big" in keywords
        assert "fan" in keywords

    def test_punctuation_removed(self):
        """Test that punctuation is properly removed."""
        text = "Hello, world! How's it going?"
        keywords = extract_keywords(text)

        assert "hello" in keywords
        assert "world" in keywords
        assert "going" in keywords

    def test_empty_text(self):
        """Test with empty text."""
        assert extract_keywords("") == set()

    def test_only_stop_words(self):
        """Test with text containing only stop words."""
        text = "the a an is are was were"
        assert extract_keywords(text) == set()


class TestCalculateSimilarity:
    """Tests for calculate_similarity function."""

    def test_identical_sets(self):
        """Test similarity of identical sets."""
        keywords = {"python", "programming", "code"}
        similarity = calculate_similarity(keywords, keywords)
        assert similarity == 1.0

    def test_completely_different(self):
        """Test similarity of completely different sets."""
        set1 = {"python", "programming"}
        set2 = {"cooking", "recipes"}
        similarity = calculate_similarity(set1, set2)
        assert similarity == 0.0

    def test_partial_overlap(self):
        """Test similarity with partial overlap."""
        set1 = {"python", "programming", "code"}
        set2 = {"python", "java", "code"}
        similarity = calculate_similarity(set1, set2)

        # Intersection: python, code (2)
        # Union: python, programming, code, java (4)
        # Similarity: 2/4 = 0.5
        assert similarity == 0.5

    def test_empty_sets(self):
        """Test with empty sets."""
        assert calculate_similarity(set(), set()) == 0.0
        assert calculate_similarity({"test"}, set()) == 0.0
        assert calculate_similarity(set(), {"test"}) == 0.0


class TestFindRelevantTimestamp:
    """Tests for find_relevant_timestamp function."""

    def test_find_matching_timestamp(self):
        """Test finding a matching timestamp."""
        timestamps = [
            {"time": 0, "topic": "Introduction", "description": "Welcome and overview"},
            {"time": 120, "topic": "Machine Learning Basics", "description": "Neural networks fundamentals"},
            {"time": 300, "topic": "Deep Learning", "description": "Advanced neural architectures"}
        ]

        answer = "Machine learning uses neural networks for pattern recognition"
        result = find_relevant_timestamp(answer, [], timestamps)

        # Should match "Machine Learning Basics" at 120 seconds
        assert result == 120

    def test_no_match_below_threshold(self):
        """Test that no match is returned below threshold."""
        timestamps = [
            {"time": 0, "topic": "Cooking recipes", "description": "Italian cuisine"}
        ]

        answer = "Programming in Python is fun"
        result = find_relevant_timestamp(answer, [], timestamps)

        assert result is None

    def test_empty_timestamps(self):
        """Test with empty timestamps list."""
        result = find_relevant_timestamp("Some answer", [], [])
        assert result is None

    def test_with_source_chunks(self):
        """Test matching with source chunks."""
        timestamps = [
            {"time": 60, "topic": "Data Science", "description": "Analytics and visualization"}
        ]

        answer = "The data shows..."
        source_chunks = ["Data science involves analytics and visualization techniques"]
        result = find_relevant_timestamp(answer, source_chunks, timestamps)

        assert result == 60

    def test_with_timestamp_keywords(self):
        """Test matching with explicit keywords in timestamps."""
        timestamps = [
            {"time": 180, "topic": "APIs", "description": "REST and GraphQL",
             "keywords": ["api", "rest", "graphql", "endpoints"]}
        ]

        answer = "REST APIs use HTTP endpoints for communication"
        result = find_relevant_timestamp(answer, [], timestamps)

        assert result == 180

    def test_custom_min_similarity(self):
        """Test with custom minimum similarity threshold."""
        timestamps = [
            {"time": 0, "topic": "Python programming", "description": "Code examples"}
        ]

        answer = "Learning to code in Python"

        # With default threshold
        result1 = find_relevant_timestamp(answer, [], timestamps)
        assert result1 == 0

        # With very high threshold
        result2 = find_relevant_timestamp(answer, [], timestamps, min_similarity=0.9)
        assert result2 is None


class TestFindRelevantTimestamps:
    """Tests for find_relevant_timestamps function."""

    def test_find_multiple_timestamps(self):
        """Test finding multiple matching timestamps."""
        timestamps = [
            {"time": 0, "topic": "Python Introduction", "description": "Getting started with Python"},
            {"time": 120, "topic": "Python Functions", "description": "Defining and using functions"},
            {"time": 240, "topic": "Python Classes", "description": "Object-oriented programming"},
            {"time": 360, "topic": "Cooking Tips", "description": "Kitchen basics"}
        ]

        answer = "Python functions and classes are fundamental programming concepts"
        results = find_relevant_timestamps(answer, [], timestamps, top_n=3)

        # Should return matches related to Python, sorted by similarity
        assert len(results) <= 3
        assert all("similarity" in r for r in results)
        assert all("time" in r for r in results)

    def test_returns_sorted_by_similarity(self):
        """Test that results are sorted by similarity descending."""
        timestamps = [
            {"time": 0, "topic": "Machine Learning", "description": "ML basics"},
            {"time": 60, "topic": "Deep Learning Neural Networks", "description": "Advanced deep learning"},
            {"time": 120, "topic": "Learning Algorithms", "description": "Algorithm design"}
        ]

        answer = "Deep learning neural networks for machine learning"
        results = find_relevant_timestamps(answer, [], timestamps, top_n=3)

        # Check descending order
        for i in range(len(results) - 1):
            assert results[i]["similarity"] >= results[i + 1]["similarity"]

    def test_respects_top_n(self):
        """Test that results are limited by top_n."""
        timestamps = [
            {"time": i * 60, "topic": f"Topic {i}", "description": "Description with Python"}
            for i in range(10)
        ]

        answer = "Python programming topic"
        results = find_relevant_timestamps(answer, [], timestamps, top_n=3)

        assert len(results) <= 3

    def test_empty_timestamps(self):
        """Test with empty timestamps list."""
        results = find_relevant_timestamps("Answer text", [], [])
        assert results == []

    def test_no_matches(self):
        """Test when no timestamps match."""
        timestamps = [
            {"time": 0, "topic": "Astronomy", "description": "Stars and galaxies"}
        ]

        answer = "Python programming is great"
        results = find_relevant_timestamps(answer, [], timestamps, min_similarity=0.5)

        assert results == []
