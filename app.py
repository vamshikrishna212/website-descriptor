import streamlit as st
from utils.config import APP_TITLE, APP_ICON, get_openai_api_key
from ui.components import show_placeholder, show_api_key_warning

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
if "compare_urls" not in st.session_state:
    st.session_state.compare_urls = ["", ""]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title(f"{APP_ICON} {APP_TITLE}")
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
if not get_openai_api_key():
    show_api_key_warning()

# ── Main area ─────────────────────────────────────────────────────────────────
st.header(f"{APP_ICON} {APP_TITLE}")
st.caption("Enter a URL in the sidebar and click **Analyze** to get started.")
st.markdown("---")

# ── Handle Analyze button ──────────────────────────────────────────────────────
if analyze_clicked:
    if not url_input.strip():
        st.error("Please enter a URL before clicking Analyze.")
    else:
        # Phase 2 will replace this block with real scraping
        with st.spinner("Scraping website… (coming in Phase 2)"):
            pass
        st.info("Scraping and analysis will be wired up in Phase 2. For now, the UI shell is complete.")

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
                st.write(summary)
            else:
                st.caption("_Summary will appear here after LLM analysis (Phase 3)._")

            st.markdown("#### ✅ Key Points")
            key_points = data.get("key_points", [])
            if key_points:
                for point in key_points:
                    st.markdown(f"- {point}")
            else:
                st.caption("_Key points will appear here after LLM analysis (Phase 3)._")

        with col2:
            st.markdown("#### 🏷️ Keywords")
            keywords = data.get("keywords", [])
            if keywords:
                st.write(" · ".join(f"`{kw}`" for kw in keywords))
            else:
                st.caption("_Keywords will appear here after Phase 5._")

            st.markdown("#### 🌍 Topics")
            topics = data.get("topics", [])
            if topics:
                for topic in topics:
                    st.badge(topic)
            else:
                st.caption("_Topics will appear here after Phase 3._")

        st.markdown("---")

        # Raw content expander
        with st.expander("📃 Raw Cleaned Content", expanded=False):
            raw = data.get("raw_text", "")
            if raw:
                st.text_area("", raw, height=300, disabled=True)
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
        st.markdown("#### 💬 Ask anything about this page")
        st.caption(
            f"Chatting about: **{st.session_state.current_data.get('url', '')}**"
        )
        st.markdown("---")

        # Render conversation history
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # Chat input
        user_input = st.chat_input("Ask a question about this page…")
        if user_input:
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)
            # Phase 4 will wire in real LLM responses here
            placeholder_reply = "Conversational Q&A with the LLM will be available in Phase 4."
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": placeholder_reply}
            )
            with st.chat_message("assistant"):
                st.write(placeholder_reply)
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

        st.markdown("#### 🔗 Links Found on Page")
        if links:
            import pandas as pd
            df_links = pd.DataFrame(links)
            st.dataframe(df_links, use_container_width=True)
        else:
            st.caption("_Links will be extracted and listed here after Phase 6._")

        st.markdown("---")
        st.markdown("#### 🖼️ Images Found on Page")
        if images:
            for img in images:
                st.markdown(f"- **{img.get('alt', '(no alt)')}** — `{img.get('src', '')}`")
        else:
            st.caption("_Images will be listed here after Phase 6._")
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
