import streamlit as st
from utils.config import (
    APP_TITLE, APP_ICON,
    get_openai_api_key, get_ollama_base_url, get_ollama_model,
    get_openrouter_api_key, OPENROUTER_MODELS,
)
from ui.components import show_placeholder, show_api_key_warning
from scraper.fetcher import fetch_html
from scraper.parser import parse_page
from scraper.cleaner import build_content
from analyzer.analysis import analyse_page, answer_question

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state initialisation ─────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []          # list of {"url": ..., "data": ...}
if "current_data" not in st.session_state:
    st.session_state.current_data = None   # analysis result for current URL
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []    # conversation history
if "analysis_error" not in st.session_state:
    st.session_state.analysis_error = None
if "llm_provider" not in st.session_state:
    st.session_state.llm_provider = "openrouter"
if "openrouter_model_label" not in st.session_state:
    st.session_state.openrouter_model_label = list(OPENROUTER_MODELS.keys())[0]


# ── Scrape helper ─────────────────────────────────────────────────────────────
def scrape_url(url: str) -> dict | None:
    """Fetch, parse, and clean a URL. Returns a data dict or None on failure."""
    try:
        html = fetch_html(url)
        parsed = parse_page(html, url)
        raw_text = build_content(parsed)
        return {
            "url": url,
            "title": parsed["title"],
            "description": parsed["description"],
            "headings": parsed["headings"],
            "paragraphs": parsed["paragraphs"],
            "links": parsed["links"],
            "images": parsed["images"],
            "raw_text": raw_text,
            # Populated by run_analysis() after scraping
            "summary": None,
            "key_points": [],
            "topics": [],
            "keywords": [],
        }
    except ValueError as exc:
        st.error(f"Invalid URL: {exc}")
    except Exception as exc:
        st.error(f"Failed to scrape **{url}**: {exc}")
    return None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title(f"{APP_ICON} {APP_TITLE}")
    st.markdown("---")
    # ── LLM Provider ─────────────────────────────────────────────────────
    st.subheader("🧠 LLM Provider")
    provider_choice = st.radio(
        "Select provider",
        options=["openrouter", "ollama", "openai"],
        index=["openrouter", "ollama", "openai"].index(st.session_state.llm_provider),
        format_func=lambda x: {
            "openrouter": "🌐 OpenRouter",
            "ollama": "🧠 Ollama (local)",
            "openai": "☁️ OpenAI",
        }[x],
        label_visibility="collapsed",
    )
    st.session_state.llm_provider = provider_choice

    if provider_choice == "openrouter":
        model_label = st.selectbox(
            "Model",
            options=list(OPENROUTER_MODELS.keys()),
            index=list(OPENROUTER_MODELS.keys()).index(st.session_state.openrouter_model_label),
            label_visibility="collapsed",
        )
        st.session_state.openrouter_model_label = model_label
        if get_openrouter_api_key():
            st.caption(f"🟢 **{model_label}** via OpenRouter")
        else:
            st.caption("🔴 No `OPENROUTER_API_KEY` in `.env`. Get one free at openrouter.ai")
    elif provider_choice == "ollama":
        st.caption(f"🟢 Using **{get_ollama_model()}** via `{get_ollama_base_url()}`")
    else:
        if get_openai_api_key():
            st.caption("🟢 OpenAI key loaded.")
        else:
            st.caption("🔴 No `OPENAI_API_KEY` found in `.env`.")

    st.markdown("---")
    # ── URL Input & Analyze ───────────────────────────────────────────────────
    st.subheader("🔍 Analyze a Website")
    url_input = st.text_input(
        "Enter URL",
        placeholder="https://example.com",
        label_visibility="collapsed",
    )
    analyze_clicked = st.button("Analyze", type="primary", use_container_width=True)

    st.markdown("---")

    # ── Compare Section ───────────────────────────────────────────────────────
    st.subheader("⚖️ Compare URLs")
    compare_url_1 = st.text_input("URL 1", placeholder="https://site-a.com", key="cmp1")
    compare_url_2 = st.text_input("URL 2", placeholder="https://site-b.com", key="cmp2")
    compare_url_3 = st.text_input("URL 3 (optional)", placeholder="https://site-c.com", key="cmp3")
    compare_clicked = st.button("Compare", use_container_width=True)

    st.markdown("---")

    # ── Session History ───────────────────────────────────────────────────────
    st.subheader("📋 History")
    if st.session_state.history:
        for i, entry in enumerate(reversed(st.session_state.history)):
            display = entry["url"][:40] + "…" if len(entry["url"]) > 40 else entry["url"]
            if st.button(display, key=f"hist_{i}", use_container_width=True):
                st.session_state.current_data = entry["data"]
                st.session_state.chat_messages = []
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("No URLs analyzed yet.")

# ── API key check ─────────────────────────────────────────────────────────────
if st.session_state.llm_provider == "openai" and not get_openai_api_key():
    show_api_key_warning()
elif st.session_state.llm_provider == "openrouter" and not get_openrouter_api_key():
    st.warning(
        "**OpenRouter API key not configured.**  \n"
        "Create a `.env` file with `OPENROUTER_API_KEY=your-key`. "
        "Get a free key at [openrouter.ai](https://openrouter.ai).",
        icon="⚠️",
    )

# ── Main area ─────────────────────────────────────────────────────────────────
st.header(f"{APP_ICON} {APP_TITLE}")
st.caption("Enter a URL in the sidebar and click **Analyze** to get started.")
st.markdown("---")

# Show persistent analysis error if one occurred on the last run
if st.session_state.get("analysis_error"):
    st.error(f"**AI analysis failed:** {st.session_state.analysis_error}", icon="🚨")

# ── Handle Analyze button ──────────────────────────────────────────────────────
if analyze_clicked:
    if not url_input.strip():
        st.error("Please enter a URL before clicking Analyze.")
    else:
        with st.spinner(f"Scraping {url_input} …"):
            data = scrape_url(url_input.strip())
        if data:
            st.session_state.analysis_error = None
            provider = st.session_state.llm_provider
            openrouter_model = OPENROUTER_MODELS.get(st.session_state.openrouter_model_label)

            # Guard: check required keys before calling LLM
            key_missing = (
                (provider == "openai" and not get_openai_api_key()) or
                (provider == "openrouter" and not get_openrouter_api_key())
            )
            if key_missing:
                st.session_state.analysis_error = (
                    f"API key for '{provider}' is not set. Add it to your .env file."
                )
            else:
                label = st.session_state.openrouter_model_label if provider == "openrouter" else provider
                with st.spinner(f"Running AI analysis with {label} …"):
                    try:
                        analysis = analyse_page(
                            data["raw_text"],
                            provider=provider,
                            openrouter_model=openrouter_model,
                        )
                        data["summary"] = analysis["summary"]
                        data["key_points"] = analysis["key_points"]
                        data["topics"] = analysis["topics"]
                    except Exception as exc:
                        st.session_state.analysis_error = str(exc)
            st.session_state.current_data = data
            st.session_state.chat_messages = []
            st.session_state.show_all_kp = False
            st.session_state.show_all_kw = False
            st.session_state.show_all_tp = False
            # Add to history (avoid duplicates)
            existing_urls = [e["url"] for e in st.session_state.history]
            if data["url"] not in existing_urls:
                st.session_state.history.append({"url": data["url"], "data": data})
            st.success(
                f"Done! **{data['title']}** — "
                f"{len(data['paragraphs'])} paragraphs, "
                f"{len(data['links'])} links, "
                f"{len(data['images'])} images."
            )
            st.rerun()

# ── Handle Compare button ──────────────────────────────────────────────────────
if compare_clicked:
    st.info("Multi-URL comparison will be available in Phase 8.")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_summary, tab_chat, tab_data, tab_compare = st.tabs(
    ["📝 Summary", "💬 Chat", "🔗 Data", "⚖️ Compare"]
)

# ── Summary Tab ───────────────────────────────────────────────────────────────
with tab_summary:
    if st.session_state.current_data:
        data = st.session_state.current_data

        # Page title & URL
        st.subheader(data.get("title", "Untitled Page"))
        st.caption(data.get("url", ""))
        st.markdown("---")

        # Summary section
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("#### 📄 Summary")
            summary = data.get("summary")
            if summary:
                # Collapse if longer than 600 chars
                if len(summary) > 600:
                    with st.expander("Read summary", expanded=False):
                        st.write(summary)
                else:
                    st.write(summary)
            else:
                st.caption("_No summary yet — make sure your OpenAI API key is set and re-analyze._")

            st.markdown("#### ✅ Key Points")
            key_points = data.get("key_points", [])
            if key_points:
                # Always show first 4; collapse the rest
                show_all_kp = st.session_state.get("show_all_kp", False)
                visible = key_points if show_all_kp else key_points[:4]
                for point in visible:
                    st.markdown(f"- {point}")
                if len(key_points) > 4:
                    label = f"▲ Show less" if show_all_kp else f"▼ Show {len(key_points) - 4} more"
                    if st.button(label, key="toggle_kp"):
                        st.session_state.show_all_kp = not show_all_kp
                        st.rerun()
            else:
                st.caption("_Key points will appear here after LLM analysis._")

        with col2:
            st.markdown("#### 🏷️ Keywords")
            keywords = data.get("keywords", [])
            if keywords:
                # Always show first 8; collapse the rest
                show_all_kw = st.session_state.get("show_all_kw", False)
                visible_kw = keywords if show_all_kw else keywords[:8]
                st.write(" · ".join(f"`{kw}`" for kw in visible_kw))
                if len(keywords) > 8:
                    label = "▲ Less" if show_all_kw else f"+{len(keywords) - 8} more"
                    if st.button(label, key="toggle_kw"):
                        st.session_state.show_all_kw = not show_all_kw
                        st.rerun()
            else:
                st.caption("_Keywords will appear here after Phase 5._")

            st.markdown("#### 🌍 Topics")
            topics = data.get("topics", [])
            if topics:
                # Always show first 5; collapse the rest
                show_all_tp = st.session_state.get("show_all_tp", False)
                visible_tp = topics if show_all_tp else topics[:5]
                for topic in visible_tp:
                    st.badge(topic)
                if len(topics) > 5:
                    label = "▲ Less" if show_all_tp else f"+{len(topics) - 5} more"
                    if st.button(label, key="toggle_tp"):
                        st.session_state.show_all_tp = not show_all_tp
                        st.rerun()
            else:
                st.caption("_Topics will appear after analysis._")

        st.markdown("---")

        # Raw content expander
        st.markdown("---")
        raw = data.get("raw_text", "")
        char_count = len(raw)
        with st.expander(f"📃 Raw Cleaned Content ({char_count:,} chars)", expanded=bool(raw)):
            if raw:
                st.text_area("", raw, height=300, disabled=True, label_visibility="collapsed")
            else:
                st.caption("_Raw content will appear here after scraping (Phase 2)._")

        # Export buttons (Phase 7)
        st.markdown("---")
        ec1, ec2, _ = st.columns([1, 1, 4])
        with ec1:
            st.button("📄 Export PDF", disabled=True, help="Available in Phase 7")
        with ec2:
            st.button("📝 Export Markdown", disabled=True, help="Available in Phase 7")

    else:
        show_placeholder(
            "Summary",
            "Analyze a URL to see the AI-generated summary, key points, topics, and keywords here.",
        )
        st.markdown("---")
        ec1, ec2, _ = st.columns([1, 1, 4])
        with ec1:
            st.button("📄 Export PDF", disabled=True, help="Available in Phase 7")
        with ec2:
            st.button("📝 Export Markdown", disabled=True, help="Available in Phase 7")

# ── Chat Tab ──────────────────────────────────────────────────────────────────
with tab_chat:
    if st.session_state.current_data:
        col_title, col_clear = st.columns([5, 1])
        with col_title:
            st.markdown("#### 💬 Ask anything about this page")
            st.caption(f"Chatting about: **{st.session_state.current_data.get('url', '')}**")
        with col_clear:
            if st.session_state.chat_messages:
                if st.button("🗑️ Clear", key="clear_chat", help="Clear conversation"):
                    st.session_state.chat_messages = []
                    st.rerun()
        st.markdown("---")

        # Render conversation history
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # Chat input
        user_input = st.chat_input("Ask a question about this page…")
        if user_input:
            # Append and show user message immediately
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)

            # Call LLM
            provider = st.session_state.llm_provider
            openrouter_model = OPENROUTER_MODELS.get(st.session_state.openrouter_model_label)
            key_missing = (
                (provider == "openai" and not get_openai_api_key()) or
                (provider == "openrouter" and not get_openrouter_api_key())
            )
            if key_missing:
                reply = f"⚠️ API key for '{provider}' is not configured. Add it to your .env file."
            else:
                with st.spinner("Thinking…"):
                    try:
                        reply = answer_question(
                            st.session_state.current_data["raw_text"],
                            st.session_state.chat_messages,  # includes user msg just appended
                            provider=provider,
                            openrouter_model=openrouter_model,
                        )
                    except Exception as exc:
                        reply = f"⚠️ Error: {exc}"

            st.session_state.chat_messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.write(reply)
    else:
        show_placeholder(
            "Chat",
            "Analyze a URL first, then come here to ask follow-up questions about the page content.",
        )

# ── Data Tab ──────────────────────────────────────────────────────────────────
with tab_data:
    if st.session_state.current_data:
        data = st.session_state.current_data
        links = data.get("links", [])
        images = data.get("images", [])

        st.markdown(f"#### 🔗 Links Found on Page — {len(links)} total")
        if links:
            import pandas as pd
            df_links = pd.DataFrame(links, columns=["href", "text", "type"])
            df_links.columns = ["URL", "Link Text", "Type"]

            filter_type = st.radio(
                "Filter:", ["All", "Internal", "External"],
                horizontal=True, key="link_filter"
            )
            if filter_type != "All":
                df_links = df_links[df_links["Type"] == filter_type.lower()]

            st.dataframe(df_links, use_container_width=True, hide_index=True)
        else:
            st.caption("_No links found on this page._")

        st.markdown("---")
        st.markdown(f"#### 🖼️ Images Found on Page — {len(images)} total")
        if images:
            import pandas as pd
            df_images = pd.DataFrame(images, columns=["src", "alt"])
            df_images.columns = ["Image URL", "Alt Text"]
            st.dataframe(df_images, use_container_width=True, hide_index=True)
        else:
            st.caption("_No images found on this page._")
    else:
        show_placeholder(
            "Data",
            "Analyze a URL to see all links and images extracted from the page.",
        )

# ── Compare Tab ───────────────────────────────────────────────────────────────
with tab_compare:
    show_placeholder(
        "Compare",
        "Enter multiple URLs in the sidebar and click **Compare** to see a side-by-side AI comparison. Available in Phase 8.",
    )
