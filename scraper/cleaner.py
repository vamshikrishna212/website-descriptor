"""Clean and combine parsed page content into a single readable text block."""

import re


def clean_text(raw_text: str) -> str:
    """Normalise whitespace and remove junk characters from a raw text string."""
    # Collapse runs of whitespace / newlines
    text = re.sub(r"\r\n|\r", "\n", raw_text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Remove zero-width and non-printable characters
    text = re.sub(r"[\u200b\u200c\u200d\ufeff\xa0]", " ", text)
    return text.strip()


def build_content(parsed: dict) -> str:
    """Combine headings and paragraphs from a parsed page dict into one text block.

    The returned string is clean, structured prose suitable for feeding to an LLM.
    """
    parts: list[str] = []

    if parsed.get("title"):
        parts.append(f"PAGE TITLE: {parsed['title']}")

    if parsed.get("description"):
        parts.append(f"DESCRIPTION: {parsed['description']}")

    if parsed.get("headings"):
        parts.append("HEADINGS:\n" + "\n".join(f"- {h}" for h in parsed["headings"]))

    if parsed.get("paragraphs"):
        parts.append("CONTENT:\n" + "\n\n".join(parsed["paragraphs"]))

    combined = "\n\n".join(parts)
    return clean_text(combined)

