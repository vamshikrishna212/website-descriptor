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
    "Gemma 4 31B": "google/gemma-4-31b-it:free",
    "Llama 3.3 70B": "meta-llama/llama-3.3-70b-instruct:free",
    "Nous: Hermes 3 405B Instruct": "nousresearch/hermes-3-llama-3.1-405b:free",
    "Liquid 2.5B": "liquid/lfm-2.5-1.2b-instruct:free",
    "Qwen 3 Coder": "qwen/qwen3-coder:free",
    "Open AI gpt-oss-120b": "openai/gpt-oss-120b:free",
}


'''
Other free models to use

Best::

Nous: Hermes 3 405B Instruct
Qwen3 Coder 480B A35B (best coding model here)
OpenAI: gpt-oss-120b
Qwen3 Next 80B A3B Instruct
Meta: Llama 3.3 70B Instruct


Tier 2::

Google: Gemma 4 31B
MoonshotAI: Kimi K2.6 (good reasoning + long context typically)
NVIDIA: Nemotron 3 Ultra
Poolside: Laguna M.1 (good for coding-focused apps)
OpenAI: gpt-oss-20b

Tier 3 ::

Google: Gemma 4 26B A4B
NVIDIA: Nemotron 3 Super
NVIDIA: Nemotron 3 Nano 30B A3B
Poolside: Laguna XS.2

for some specific purpose ::

NVIDIA: Llama Nemotron Rerank VL 1B V2 → ranking search results
NVIDIA: Llama Nemotron Embed VL 1B V2 → embeddings
NVIDIA: Nemotron 3.5 Content Safety → moderation


Others::

NVIDIA: Llama Nemotron Rerank VL 1B V2
Nex AGI: Nex-N2-Pro
NVIDIA: Nemotron 3.5 Content Safety
NVIDIA: Nemotron 3 Ultra
NVIDIA: Nemotron 3 Nano Omni
Poolside: Laguna XS.2 
Poolside: Laguna M.1
MoonshotAI: Kimi K2.6
Google: Gemma 4 26B A4B
Google: Gemma 4 31B
NVIDIA: Nemotron 3 Super
NVIDIA: Llama Nemotron Embed VL 1B V2
LiquidAI: LFM2.5-1.2B-Thinking
LiquidAI: LFM2.5-1.2B-Instruct
NVIDIA: Nemotron 3 Nano 30B A3B
NVIDIA: Nemotron Nano 12B 2 VL
Qwen: Qwen3 Next 80B A3B Instruct
NVIDIA: Nemotron Nano 9B V2 
OpenAI: gpt-oss-120b
OpenAI: gpt-oss-20b
Qwen: Qwen3 Coder 480B A35B
Venice: Uncensored
Meta: Llama 3.3 70B Instruct
Meta: Llama 3.2 3B Instruct
Nous: Hermes 3 405B Instruct

'''
# ── App-wide constants ────────────────────────────────────────────────────────
APP_TITLE = "Website Descriptor"
APP_ICON = "🌐"
APP_VERSION = "1.0.0"
MAX_CONTENT_CHARS = 12000  # max chars sent to LLM context
REQUEST_TIMEOUT = 20       # seconds for HTTP requests
