"""Orchestrates all LLM analysis tasks against scraped page content."""

import json
from analyzer.llm_client import chat
from analyzer.prompts import summary_messages, key_points_messages, topics_messages
from utils.text_utils import chunk_text
from utils.config import MAX_CONTENT_CHARS


def _truncate(content: str) -> str:
    """Trim content to the max chars the LLM context allows."""
    chunks = chunk_text(content, MAX_CONTENT_CHARS)
    return chunks[0] if chunks else content


def _parse_json_list(raw: str) -> list[str]:
    """Safely parse a JSON array string returned by the LLM."""
    raw = raw.strip()
    # Strip any accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        result = json.loads(raw)
        if isinstance(result, list):
            return [str(item).strip() for item in result if item]
    except json.JSONDecodeError:
        pass
    # Fallback: split by newline and strip bullets
    lines = [ln.lstrip("-•* ").strip() for ln in raw.splitlines() if ln.strip()]
    return lines


def analyse_page(content: str, provider: str = "openai") -> dict:
    """Run summary, key_points, and topics analysis against *content*.

    Args:
        content:  Cleaned page text.
        provider: 'openai' or 'ollama'.

    Returns::

        {
            "summary":    str,
            "key_points": list[str],
            "topics":     list[str],
        }
    """
    trimmed = _truncate(content)

    summary = chat(summary_messages(trimmed), provider=provider)
    key_points_raw = chat(key_points_messages(trimmed), provider=provider)
    topics_raw = chat(topics_messages(trimmed), provider=provider)

    return {
        "summary": summary.strip(),
        "key_points": _parse_json_list(key_points_raw),
        "topics": _parse_json_list(topics_raw),
    }


