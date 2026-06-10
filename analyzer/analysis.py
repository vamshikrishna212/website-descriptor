"""Orchestrates all LLM analysis tasks against scraped page content."""

import json
import time
from analyzer.llm_client import chat, RateLimitRetryError
from analyzer.prompts import summary_messages, key_points_messages, topics_messages
from utils.text_utils import chunk_text
from utils.config import MAX_CONTENT_CHARS

_MAX_RETRIES = 3


def _chat_with_retry(
    messages: list[dict],
    provider: str,
    openrouter_model: str | None,
) -> str:
    """Call chat(), automatically waiting and retrying on 429 rate-limit errors."""
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            return chat(messages, provider=provider, openrouter_model=openrouter_model)
        except RateLimitRetryError as exc:
            if attempt == _MAX_RETRIES:
                raise exc.original
            time.sleep(exc.wait_seconds)
    return ""  # unreachable


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


def analyse_page(content: str, provider: str = "openai", openrouter_model: str | None = None) -> dict:
    """Run summary, key_points, and topics analysis against *content*.

    Args:
        content:           Cleaned page text.
        provider:          'openai', 'ollama', or 'openrouter'.
        openrouter_model:  OpenRouter model ID (used only when provider='openrouter').

    Returns::

        {
            "summary":    str,
            "key_points": list[str],
            "topics":     list[str],
        }
    """
    trimmed = _truncate(content)

    summary = _chat_with_retry(summary_messages(trimmed), provider=provider, openrouter_model=openrouter_model)
    key_points_raw = _chat_with_retry(key_points_messages(trimmed), provider=provider, openrouter_model=openrouter_model)
    topics_raw = _chat_with_retry(topics_messages(trimmed), provider=provider, openrouter_model=openrouter_model)

    return {
        "summary": summary.strip(),
        "key_points": _parse_json_list(key_points_raw),
        "topics": _parse_json_list(topics_raw),
    }


