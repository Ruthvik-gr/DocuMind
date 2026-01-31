"""
Timestamp matcher utility for matching chat answers to relevant timestamps.
"""
from typing import List, Optional, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)


def extract_keywords(text: str) -> set:
    """
    Extract meaningful keywords from text.

    Args:
        text: Text to extract keywords from

    Returns:
        Set of lowercase keywords
    """
    # Remove punctuation and convert to lowercase
    text = re.sub(r'[^\w\s]', ' ', text.lower())

    # Split into words
    words = text.split()

    # Filter out common stop words
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
        'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above',
        'below', 'between', 'under', 'again', 'further', 'then', 'once',
        'here', 'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
        'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
        'own', 'same', 'so', 'than', 'too', 'very', 'just', 'and', 'but',
        'if', 'or', 'because', 'until', 'while', 'about', 'against', 'this',
        'that', 'these', 'those', 'it', 'its', 'what', 'which', 'who', 'whom',
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you',
        'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
        'she', 'her', 'hers', 'herself', 'they', 'them', 'their', 'theirs'
    }

    # Keep words with at least 3 characters and not in stop words
    keywords = {word for word in words if len(word) >= 3 and word not in stop_words}

    return keywords


def calculate_similarity(keywords1: set, keywords2: set) -> float:
    """
    Calculate Jaccard similarity between two keyword sets.

    Args:
        keywords1: First set of keywords
        keywords2: Second set of keywords

    Returns:
        Similarity score between 0 and 1
    """
    if not keywords1 or not keywords2:
        return 0.0

    intersection = keywords1.intersection(keywords2)
    union = keywords1.union(keywords2)

    return len(intersection) / len(union) if union else 0.0


def find_relevant_timestamp(
    answer: str,
    source_chunks: List[str],
    timestamps: List[Dict[str, Any]],
    min_similarity: float = 0.1
) -> Optional[int]:
    """
    Match answer content to the closest topic timestamp using keyword overlap.

    Args:
        answer: The answer text from the chat response
        source_chunks: List of source document chunks used to generate the answer
        timestamps: List of timestamp entries with 'time', 'topic', 'description', 'keywords'
        min_similarity: Minimum similarity threshold to return a match

    Returns:
        Timestamp in seconds of the most relevant topic, or None if no match
    """
    if not timestamps:
        return None

    # Combine answer and source chunks for keyword extraction
    combined_text = answer
    if source_chunks:
        combined_text += " " + " ".join(source_chunks)

    answer_keywords = extract_keywords(combined_text)

    if not answer_keywords:
        return None

    best_match_time = None
    best_similarity = min_similarity

    for ts in timestamps:
        # Combine topic, description, and keywords for comparison
        ts_text = ts.get('topic', '')
        if ts.get('description'):
            ts_text += ' ' + ts.get('description', '')

        # Add explicit keywords if available
        ts_keywords_list = ts.get('keywords', [])
        if ts_keywords_list:
            ts_text += ' ' + ' '.join(ts_keywords_list)

        ts_keywords = extract_keywords(ts_text)

        similarity = calculate_similarity(answer_keywords, ts_keywords)

        if similarity > best_similarity:
            best_similarity = similarity
            best_match_time = ts.get('time')

    if best_match_time is not None:
        logger.debug(f"Found matching timestamp: {best_match_time}s with similarity {best_similarity:.2f}")

    return best_match_time


def find_relevant_timestamps(
    answer: str,
    source_chunks: List[str],
    timestamps: List[Dict[str, Any]],
    top_n: int = 3,
    min_similarity: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Find multiple relevant timestamps sorted by relevance.

    Args:
        answer: The answer text from the chat response
        source_chunks: List of source document chunks used to generate the answer
        timestamps: List of timestamp entries
        top_n: Number of top matches to return
        min_similarity: Minimum similarity threshold

    Returns:
        List of matching timestamps with similarity scores
    """
    if not timestamps:
        return []

    # Combine answer and source chunks
    combined_text = answer
    if source_chunks:
        combined_text += " " + " ".join(source_chunks)

    answer_keywords = extract_keywords(combined_text)

    if not answer_keywords:
        return []

    matches = []

    for ts in timestamps:
        ts_text = ts.get('topic', '')
        if ts.get('description'):
            ts_text += ' ' + ts.get('description', '')

        ts_keywords_list = ts.get('keywords', [])
        if ts_keywords_list:
            ts_text += ' ' + ' '.join(ts_keywords_list)

        ts_keywords = extract_keywords(ts_text)
        similarity = calculate_similarity(answer_keywords, ts_keywords)

        if similarity >= min_similarity:
            matches.append({
                'time': ts.get('time'),
                'topic': ts.get('topic'),
                'similarity': similarity
            })

    # Sort by similarity (descending)
    matches.sort(key=lambda x: x['similarity'], reverse=True)

    return matches[:top_n]
