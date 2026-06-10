"""Placeholder stubs for reusable Streamlit UI components (populated in later phases)."""
import streamlit as st


def show_placeholder(tab_name: str, description: str) -> None:
    """Render a styled placeholder card for tabs not yet implemented."""
    st.info(f"**{tab_name}** — {description}\n\n_This section will be available after scraping a URL._")


def show_api_key_warning() -> None:
    """Show a warning banner when the OpenAI API key is missing."""
    st.warning(
        "**OpenAI API key not configured.**  \n"
        "Create a `.env` file with `OPENAI_API_KEY=your-key` to enable AI features.",
        icon="⚠️",
    )
