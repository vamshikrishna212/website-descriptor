"""Fetch raw HTML from a URL with proper headers and error handling."""

import requests
from utils.config import REQUEST_TIMEOUT


# Realistic browser headers to avoid basic bot-blocking
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def fetch_html(url: str, timeout: int = REQUEST_TIMEOUT) -> str:
    """Fetch raw HTML from *url* and return it as a UTF-8 string.

    Raises:
        ValueError: if the URL scheme is not http/https.
        requests.RequestException: on network/HTTP errors.
    """
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid URL scheme. URL must start with http:// or https://: {url}")

    response = requests.get(url, headers=_HEADERS, timeout=timeout, allow_redirects=True)
    response.raise_for_status()

    # Respect charset from the response; fall back to apparent encoding
    if response.encoding is None or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding or "utf-8"

    return response.text

