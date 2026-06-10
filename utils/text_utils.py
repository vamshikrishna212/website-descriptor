"""Text utility functions for chunking and keyword extraction."""

import re
from collections import Counter
import spacy


def chunk_text(text: str, max_chars: int = 12000) -> list[str]:
    """Split text into chunks that fit within the LLM context window."""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:max_chars])
        text = text[max_chars:]
    return chunks


# ── Keyword Extraction (spaCy noun chunks) ────────────────────────────────

# Load once at import time — only the components we need (faster, less RAM)
_nlp = spacy.load("en_core_web_sm", disable=["ner", "textcat"])
_nlp.max_length = 2_000_000

# Noise phrases that spaCy legitimately parses as noun chunks but are useless
_NOISE: frozenset[str] = frozenset({
    "page", "pages", "site", "website", "content", "click", "link", "links",
    "menu", "footer", "header", "navigation", "nav", "cookie", "cookies",
    "privacy", "terms", "read more", "learn more", "see more", "view more",
    "external links", "references", "see also", "further reading",
    "table of contents", "edit", "source", "jump", "top",
})


def _clean_chunk(text: str) -> str:
    """Normalise a noun chunk: lowercase, strip leading articles/determiners."""
    text = text.lower().strip()
    # Strip leading articles / possessives ("the climate", "a new approach")
    text = re.sub(r'^(the|a|an|this|that|these|those|its|their|our|his|her)\s+', '', text)
    return text.strip()


def extract_keywords(text: str, top_n: int = 20) -> list[str]:
    """Extract significant keywords and phrases from *text* using spaCy noun chunks.

    Parses the text with a lightweight spaCy pipeline, collects noun phrases,
    filters noise, deduplicates, and returns the most frequent ones.

    Args:
        text:   Raw/cleaned page text.
        top_n:  Maximum number of keywords to return.

    Returns:
        Ordered list of keyword strings (most frequent / significant first).
    """
    if not text or not text.strip():
        return []

    try:
        # Limit to first 100 000 chars to keep latency low on huge pages
        doc = _nlp(text[:100_000])

        chunks: list[str] = []
        for chunk in doc.noun_chunks:
            cleaned = _clean_chunk(chunk.text)
            # Keep phrases: 2–40 chars, at least 2 chars after cleaning, not pure noise
            if (
                2 <= len(cleaned) <= 40
                and cleaned not in _NOISE
                and not cleaned.isdigit()
            ):
                chunks.append(cleaned)

        if not chunks:
            return []

        # Rank by frequency; surface the most recurring concepts first
        freq: Counter = Counter(chunks)

        # Deduplicate: if a shorter phrase is a substring of a more frequent
        # longer phrase, prefer the longer one
        ranked = [kw for kw, _ in freq.most_common()]
        seen_tokens: set[str] = set()
        result: list[str] = []
        for phrase in ranked:
            words = set(phrase.split())
            # Skip if all words already covered by a higher-ranked phrase
            if words.issubset(seen_tokens):
                continue
            result.append(phrase)
            seen_tokens.update(words)
            if len(result) == top_n:
                break

        return result

    except Exception:
        return []
