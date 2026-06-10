"""Placeholder stubs for export helpers (PDF / Markdown) — implemented in Phase 7."""


def to_markdown(data: dict) -> str:
    """Convert analysis results dict to a Markdown string."""
    lines = [f"# {data.get('title', 'Website Analysis')}\n"]
    if data.get("url"):
        lines.append(f"**URL:** {data['url']}\n")
    if data.get("summary"):
        lines.append(f"## Summary\n{data['summary']}\n")
    if data.get("key_points"):
        lines.append("## Key Points\n")
        for point in data["key_points"]:
            lines.append(f"- {point}")
    return "\n".join(lines)


def to_pdf(data: dict) -> bytes:
    """Convert analysis results dict to PDF bytes. Stub — returns empty bytes."""
    return b""
