import os
from dotenv import load_dotenv

load_dotenv(override=True)


# ── OpenAI ────────────────────────────────────────────────────────────────────
def get_openai_api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "")


def get_openai_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ── Ollama ────────────────────────────────────────────────────────────────────
def get_ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")


def get_ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", "gemma3:270m")


# ── OpenRouter ────────────────────────────────────────────────────────────────
def get_openrouter_api_key() -> str:
    return os.getenv("OPENROUTER_API_KEY", "")


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Available free/affordable models on OpenRouter shown in the UI
OPENROUTER_MODELS: dict[str, str] = {
    "Gemma 4 31B (free)": "google/gemma-4-31b-it:free",
    "Llama 3.3 70B (free)": "meta-llama/llama-3.3-70b-instruct:free",
    "NVIDIA: Nemotron 3 Super (free)": "nvidia/nemotron-3-super-120b-a12b:free",
    "Liquid 2.5B (free)": "liquid/lfm-2.5-1.2b-instruct:free"
}


# ── App-wide constants ────────────────────────────────────────────────────────
APP_TITLE = "Website Descriptor"
APP_ICON = "🌐"
MAX_CONTENT_CHARS = 12000  # max chars sent to LLM context
REQUEST_TIMEOUT = 15       # seconds for HTTP requests
