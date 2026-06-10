import os
from dotenv import load_dotenv

load_dotenv()


def get_openai_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "")
    return key


def get_openai_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# App-wide constants
APP_TITLE = "Website Descriptor"
APP_ICON = "🌐"
MAX_CONTENT_CHARS = 12000  # max chars sent to LLM context
REQUEST_TIMEOUT = 15       # seconds for HTTP requests
