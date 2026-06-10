"""Placeholder — implemented in Phase 2."""


def parse_page(html: str, url: str) -> dict:
    """Parse HTML and return structured content dict.

    Returns:
        {
            "title": str,
            "headings": list[str],
            "paragraphs": list[str],
            "links": list[{"href": str, "text": str, "type": str}],
            "images": list[{"src": str, "alt": str}],
            "meta": dict,
        }
    """
    raise NotImplementedError("Phase 2")
