"""LLM client supporting OpenAI and local Ollama (OpenAI-compatible API)."""

from openai import OpenAI
from utils.config import (
    get_openai_api_key,
    get_openai_model,
    get_ollama_base_url,
    get_ollama_model,
)

# Cached clients per provider
_clients: dict[str, OpenAI] = {}


def get_client(provider: str = "openai") -> OpenAI:
    """Return a cached OpenAI-SDK client for *provider* ('openai' or 'ollama').

    Raises:
        ValueError: if an unknown provider is given.
        RuntimeError: if OPENAI_API_KEY is not set when using OpenAI.
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
        # Ollama's OpenAI-compatible endpoint — no real API key needed
        _clients[provider] = OpenAI(
            base_url=get_ollama_base_url(),
            api_key="ollama",          # required by the SDK but not validated by Ollama
        )

    else:
        raise ValueError(f"Unknown provider '{provider}'. Choose 'openai' or 'ollama'.")

    return _clients[provider]


def get_model(provider: str = "openai") -> str:
    """Return the configured model name for the given provider."""
    if provider == "ollama":
        return get_ollama_model()
    return get_openai_model()


def chat(messages: list[dict], provider: str = "openai", temperature: float = 0.3) -> str:
    """Send *messages* to the LLM and return the reply text.

    Args:
        messages:    OpenAI-format message list.
        provider:    'openai' or 'ollama'.
        temperature: Sampling temperature.
    """
    client = get_client(provider)
    response = client.chat.completions.create(
        model=get_model(provider),
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""

