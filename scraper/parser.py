"""Parse raw HTML into structured content using BeautifulSoup."""

from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


# Tags whose entire subtree we drop before extracting text
_NOISE_TAGS = [
    "script", "style", "noscript", "iframe", "nav", "footer",
    "header", "aside", "form", "button", "svg",
    "advertisement", "ads",
]


def parse_page(html: str, url: str) -> dict:
    """Parse *html* and return a structured content dict.

    Returns::

        {
            "title":      str,
            "description": str,
            "headings":   list[str],
            "paragraphs": list[str],
            "links":      list[{"href": str, "text": str, "type": str}],
            "images":     list[{"src": str, "alt": str}],
            "meta":       dict[str, str],
        }
    """
    soup = BeautifulSoup(html, "lxml")
    base_domain = urlparse(url).netloc

    # ── Meta ──────────────────────────────────────────────────────────────────
    meta: dict[str, str] = {}
    for tag in soup.find_all("meta"):
        name = tag.get("name") or tag.get("property") or ""
        content = tag.get("content") or ""
        if name and content:
            meta[name.lower()] = content

    # ── Title ─────────────────────────────────────────────────────────────────
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else meta.get("og:title", "Untitled")

    description = (
        meta.get("description")
        or meta.get("og:description")
        or ""
    )

    # ── Remove noise before text extraction ───────────────────────────────────
    for tag in soup.find_all(_NOISE_TAGS):
        tag.decompose()

    # ── Headings ─────────────────────────────────────────────────────────────
    headings: list[str] = []
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = h.get_text(separator=" ", strip=True)
        if text:
            headings.append(text)

    # ── Paragraphs ────────────────────────────────────────────────────────────
    paragraphs: list[str] = []
    for p in soup.find_all("p"):
        text = p.get_text(separator=" ", strip=True)
        if len(text) > 40:          # skip very short / decorative fragments
            paragraphs.append(text)

    # ── List items ────────────────────────────────────────────────────────────
    # Collect top-level <ul>/<ol> blocks (skip lists nested inside another list
    # to avoid duplicating items already captured by the parent)
    list_groups: list[list[str]] = []
    for lst in soup.find_all(["ul", "ol"]):
        if lst.parent and lst.parent.name in ("ul", "ol", "li"):
            continue  # nested list — parent already handles it
        items = []
        for li in lst.find_all("li"):
            text = li.get_text(separator=" ", strip=True)
            if text and len(text) > 3:
                items.append(text)
        if len(items) >= 2:  # ignore trivially small lists (nav remnants etc.)
            list_groups.append(items)

    # ── Code blocks ───────────────────────────────────────────────────────────
    code_blocks: list[str] = []
    for pre in soup.find_all("pre"):
        text = pre.get_text(separator="\n", strip=True)
        if text and len(text) > 10:
            code_blocks.append(text)

    # ── Links ─────────────────────────────────────────────────────────────────
    links: list[dict] = []
    seen_hrefs: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:")):
            continue
        absolute = urljoin(url, href)
        if absolute in seen_hrefs:
            continue
        seen_hrefs.add(absolute)
        link_domain = urlparse(absolute).netloc
        link_type = "internal" if link_domain == base_domain else "external"
        text = a.get_text(separator=" ", strip=True) or absolute
        links.append({"href": absolute, "text": text[:120], "type": link_type})

    # ── Images ────────────────────────────────────────────────────────────────
    images: list[dict] = []
    seen_srcs: set[str] = set()
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        if not src or src in seen_srcs:
            continue
        seen_srcs.add(src)
        absolute_src = urljoin(url, src)
        alt = img.get("alt", "").strip()
        images.append({"src": absolute_src, "alt": alt})

    return {
        "title": title,
        "description": description,
        "headings": headings,
        "paragraphs": paragraphs,
        "list_groups": list_groups,
        "code_blocks": code_blocks,
        "links": links,
        "images": images,
        "meta": meta,
    }

