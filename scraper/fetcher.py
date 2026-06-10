"""Fetch raw HTML from a URL with proper headers and error handling."""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse
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
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
}

# Domains known to actively block scrapers
_BLOCKED_DOMAINS: frozenset[str] = frozenset({
    "medium.com",
    "twitter.com", "x.com",
    "facebook.com", "instagram.com",
    "linkedin.com",
    "netflix.com",
    "cloudflare.com",
})


def _make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(_HEADERS)
    return session


def validate_url(url: str) -> str:
    """Validate and normalise a URL string.

    Returns the cleaned URL.
    Raises ValueError with a user-friendly message on any problem.
    """
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty.")
    if not url.startswith(("http://", "https://")):
        # Try prepending https://
        url = "https://" + url
    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError(f"Could not parse a valid hostname from: {url!r}")
    domain = parsed.netloc.lower().removeprefix("www.")
    if domain in _BLOCKED_DOMAINS:
        raise ValueError(
            f"**{domain}** actively blocks scrapers and cannot be fetched. "
            "Try a different URL."
        )
    return url


def fetch_html(url: str, timeout: int = REQUEST_TIMEOUT) -> str:
    """Fetch raw HTML from *url* and return it as a UTF-8 string.

    Raises:
        ValueError: if the URL is invalid or the domain is blocked.
        requests.RequestException: on network/HTTP errors.
    """
    url = validate_url(url)

    session = _make_session()
    try:
        response = session.get(url, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise requests.exceptions.ConnectionError(
            f"Could not connect to **{urlparse(url).netloc}**. "
            "Check the URL and your internet connection."
        )
    except requests.exceptions.Timeout:
        raise requests.exceptions.Timeout(
            f"Request timed out after {timeout}s fetching **{url}**."
        )
    except requests.exceptions.HTTPError as exc:
        code = exc.response.status_code if exc.response is not None else "?"
        raise requests.exceptions.HTTPError(
            f"HTTP {code} error fetching **{url}**."
        )

    # Respect charset from the response; fall back to apparent encoding
    if response.encoding is None or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding or "utf-8"

    return response.text

