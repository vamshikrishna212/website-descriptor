"""Prompt templates for each analysis type."""


def summary_messages(content: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "You are an expert at analysing web page content. "
                "Write a clear, concise summary (3–5 sentences) of the page provided by the user. "
                "Focus on the main purpose, key information, and what a reader would take away."
            ),
        },
        {"role": "user", "content": f"Analyse this web page content:\n\n{content}"},
    ]


def key_points_messages(content: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "You are an expert at extracting the most important points from web content. "
                "Return ONLY a JSON array of strings — each string is one key point. "
                "Aim for 5–8 concise bullet points. No markdown, no extra text, just the JSON array."
            ),
        },
        {"role": "user", "content": f"Extract the key points from:\n\n{content}"},
    ]


def topics_messages(content: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "You are an expert at topic classification. "
                "Return ONLY a JSON array of short topic labels (1–3 words each) that best describe the content. "
                "Aim for 3–6 topics. No markdown, no extra text, just the JSON array."
            ),
        },
        {"role": "user", "content": f"Identify the main topics of:\n\n{content}"},
    ]


def qa_messages(content: str, conversation: list[dict]) -> list[dict]:
    """Build the full message list for conversational Q&A (Phase 4)."""
    system = {
        "role": "system",
        "content": (
            "You are a helpful assistant that answers questions about the following web page content. "
            "Answer only based on the content provided. If the answer is not in the content, say so clearly.\n\n"
            f"WEB PAGE CONTENT:\n{content}"
        ),
    }
    return [system] + conversation


def comparison_messages(contents: list[tuple[str, str]]) -> list[dict]:
    """Build messages for multi-URL comparison (Phase 8)."""
    pages_block = "\n\n".join(
        f"--- PAGE {i+1}: {url} ---\n{text}"
        for i, (url, text) in enumerate(contents)
    )
    return [
        {
            "role": "system",
            "content": (
                "You are an expert analyst. Compare the web pages provided and write a structured comparison covering: "
                "main purpose, key similarities, key differences, and a brief verdict on which is more informative."
            ),
        },
        {"role": "user", "content": f"Compare these web pages:\n\n{pages_block}"},
    ]
