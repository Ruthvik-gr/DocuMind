"""
Text processing utilities.
"""
import re


def count_words(text: str) -> int:
    """Count words in text."""
    if not text:
        return 0
    # Split on whitespace and filter empty strings
    words = [word for word in re.split(r'\s+', text.strip()) if word]
    return len(words)


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)

    return text.strip()


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
