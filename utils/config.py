import os
from dotenv import load_dotenv

load_dotenv()


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


# ── App-wide constants ────────────────────────────────────────────────────────
APP_TITLE = "Website Descriptor"
APP_ICON = "🌐"
MAX_CONTENT_CHARS = 12000  # max chars sent to LLM context
REQUEST_TIMEOUT = 15       # seconds for HTTP requests
