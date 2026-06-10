"""Placeholder stubs for future text utility functions."""


def chunk_text(text: str, max_chars: int = 12000) -> list[str]:
    """Split text into chunks that fit within the LLM context window."""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:max_chars])
        text = text[max_chars:]
    return chunks


def extract_keywords(text: str, top_n: int = 15) -> list[str]:
    """Placeholder — returns empty list until Phase 5 implements extraction."""
    return []
