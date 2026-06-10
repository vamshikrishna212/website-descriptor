"""Reusable Streamlit UI components."""
import streamlit as st


def show_placeholder(tab_name: str, description: str) -> None:
    """Render a styled placeholder card for empty tab states."""
    st.markdown(
        f"""
        <div style="
            border: 1.5px dashed #444;
            border-radius: 10px;
            padding: 2.5rem 2rem;
            text-align: center;
            color: #888;
            margin: 2rem 0;
        ">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔍</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: #ccc; margin-bottom: 0.4rem;">{tab_name}</div>
            <div style="font-size: 0.9rem;">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_api_key_warning() -> None:
    """Show a warning banner when the OpenAI API key is missing."""
    st.warning(
        "**OpenAI API key not configured.**  \n"
        "Create a `.env` file with `OPENAI_API_KEY=your-key` to enable AI features.",
        icon="⚠️",
    )


def show_analysis_progress(step: int, total: int, label: str) -> None:
    """Show a labelled progress bar for multi-step LLM analysis."""
    st.progress(step / total, text=f"Step {step}/{total} — {label}")


def show_scrape_stats(data: dict) -> None:
    """Show a compact inline stats row for a freshly scraped page."""
    st.success(
        f"✅ **{data.get('title', 'Untitled')}**  \n"
        f"📄 {len(data.get('paragraphs', []))} paragraphs · "
        f"🔗 {len(data.get('links', []))} links · "
        f"🖼️ {len(data.get('images', []))} images · "
        f"📝 {len(data.get('raw_text', '')):,} chars"
    )
