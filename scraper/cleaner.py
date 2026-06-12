"""Clean and combine parsed page content into a single readable text block."""

import re


def clean_text(raw_text: str) -> str:
    """Normalise whitespace and remove junk characters from a raw text string."""
    # Collapse runs of whitespace / newlines
    text = re.sub(r"\r\n|\r", "\n", raw_text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Remove zero-width and non-printable characters
    text = re.sub(r"[\u200b\u200c\u200d\ufeff\xa0]", " ", text)
    return text.strip()


def build_content(parsed: dict) -> str:
    """Combine all extracted content from a parsed page dict into one text block.

    The returned string is clean, structured prose suitable for feeding to an LLM.
    """
    parts: list[str] = []

    if parsed.get("title"):
        parts.append(f"PAGE TITLE: {parsed['title']}")

    if parsed.get("description"):
        parts.append(f"DESCRIPTION: {parsed['description']}")

    if parsed.get("headings"):
        parts.append("HEADINGS:\n" + "\n".join(f"- {h}" for h in parsed["headings"]))

    if parsed.get("paragraphs"):
        parts.append("CONTENT:\n" + "\n\n".join(parsed["paragraphs"]))

    if parsed.get("list_groups"):
        lists_text = []
        for group in parsed["list_groups"]:
            lists_text.append("\n".join(f"- {item}" for item in group))
        parts.append("LISTS:\n" + "\n\n".join(lists_text))

    if parsed.get("code_blocks"):
        blocks_text = []
        for i, block in enumerate(parsed["code_blocks"], 1):
            # Truncate each individual code block to avoid blowing the context
            truncated = block[:800] + "\n... (truncated)" if len(block) > 800 else block
            blocks_text.append(f"[Code Block {i}]\n{truncated}")
        parts.append("CODE EXAMPLES:\n" + "\n\n".join(blocks_text))

    if parsed.get("tables"):
        table_parts = []
        for t in parsed["tables"]:
            headers = t.get("headers", [])
            rows = t.get("rows", [])
            if not headers and not rows:
                continue
            # Determine column count
            col_count = max(len(headers), max((len(r) for r in rows), default=0))
            if col_count == 0:
                continue
            lines = []
            if headers:
                # Pad headers to col_count
                padded = headers + [""] * (col_count - len(headers))
                lines.append("| " + " | ".join(padded) + " |")
                lines.append("| " + " | ".join("---" for _ in range(col_count)) + " |")
            for row in rows:
                padded = row + [""] * (col_count - len(row))
                lines.append("| " + " | ".join(padded[:col_count]) + " |")
            table_parts.append("\n".join(lines))
        if table_parts:
            parts.append("TABLES:\n" + "\n\n".join(table_parts))

    if parsed.get("span_facts"):
        # Cap to 60 entries and deduplicate to avoid bloating the context
        seen: set[str] = set()
        unique_facts = []
        for fact in parsed["span_facts"]:
            key = fact[:80]
            if key not in seen:
                seen.add(key)
                unique_facts.append(fact)
            if len(unique_facts) >= 60:
                break
        parts.append("KEY FACTS:\n" + "\n".join(f"• {f}" for f in unique_facts))

    combined = "\n\n".join(parts)
    return clean_text(combined)

