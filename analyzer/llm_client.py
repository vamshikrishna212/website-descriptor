"""LLM client supporting OpenAI, local Ollama, and OpenRouter."""

import time
from openai import OpenAI, RateLimitError
from utils.config import (
    get_openai_api_key,
    get_openai_model,
    get_ollama_base_url,
    get_ollama_model,
    get_openrouter_api_key,
    OPENROUTER_BASE_URL,
)

# Cached clients keyed by provider
_clients: dict[str, OpenAI] = {}

_DEFAULT_RETRY_WAIT = 35  # fallback seconds if OpenRouter doesn't tell us how long


class RateLimitRetryError(Exception):
    """Raised when a 429 is hit so the caller can surface the wait time."""
    def __init__(self, message: str, wait_seconds: float, original: Exception):
        super().__init__(message)
        self.wait_seconds = wait_seconds
        self.original = original


def _extract_retry_after(exc: RateLimitError) -> float:
    """Extract retry_after_seconds from OpenRouter's error metadata."""
    try:
        body = exc.response.json()
        seconds = body.get("error", {}).get("metadata", {}).get("retry_after_seconds")
        if seconds is not None:
            return float(seconds) + 2  # small buffer
    except Exception:
        pass
    return _DEFAULT_RETRY_WAIT


def get_client(provider: str = "openai") -> OpenAI:
    """Return a cached OpenAI-SDK client for *provider*.

    Supported providers: 'openai', 'ollama', 'openrouter'.

    Raises:
        ValueError: unknown provider.
        RuntimeError: required API key not set.
    """
    if provider in _clients:
        return _clients[provider]

    if provider == "openai":
        api_key = get_openai_api_key()
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Add it to your .env file."
            )
        _clients[provider] = OpenAI(api_key=api_key)

    elif provider == "ollama":
        _clients[provider] = OpenAI(
            base_url=get_ollama_base_url(),
            api_key="ollama",   # required by SDK, not validated by Ollama
        )

    elif provider == "openrouter":
        api_key = get_openrouter_api_key()
        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Add it to your .env file. "
                "Get a free key at https://openrouter.ai"
            )
        _clients[provider] = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "http://localhost:8501",  # required by OpenRouter
                "X-Title": "Website Descriptor",
            },
        )

    else:
        raise ValueError(
            f"Unknown provider '{provider}'. Choose 'openai', 'ollama', or 'openrouter'."
        )

    return _clients[provider]


def get_model(provider: str = "openai", openrouter_model: str | None = None) -> str:
    """Return the model name to use for the given provider."""
    if provider == "ollama":
        return get_ollama_model()
    if provider == "openrouter":
        return openrouter_model or "deepseek/deepseek-chat-v3-0324:free"
    return get_openai_model()


def chat(
    messages: list[dict],
    provider: str = "openai",
    openrouter_model: str | None = None,
    temperature: float = 0.3,
) -> str:
    """Send *messages* to the LLM and return the reply text.

    On a 429 rate-limit response, raises RateLimitRetryError with the
    number of seconds the caller should wait before retrying.

    Args:
        messages:          OpenAI-format message list.
        provider:          'openai', 'ollama', or 'openrouter'.
        openrouter_model:  Model ID to use when provider is 'openrouter'.
        temperature:       Sampling temperature.
    """
    client = get_client(provider)
    try:
        response = client.chat.completions.create(
            model=get_model(provider, openrouter_model),
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
    except RateLimitError as exc:
        wait = _extract_retry_after(exc)
        raise RateLimitRetryError(
            f"Rate limited by '{provider}'. Retrying in {wait:.0f}s…",
            wait_seconds=wait,
            original=exc,
        ) from exc


