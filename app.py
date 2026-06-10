import streamlit as st
from datetime import datetime
from utils.config import (
    APP_TITLE, APP_ICON,
    get_openai_api_key, get_ollama_base_url, get_ollama_model,
    get_openrouter_api_key, OPENROUTER_MODELS,
)
from ui.components import show_placeholder, show_api_key_warning
from ui.export import to_markdown, to_pdf
from scraper.fetcher import fetch_html
from scraper.parser import parse_page
from scraper.cleaner import build_content
from analyzer.analysis import analyse_page, answer_question, compare_pages

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
if "links_visible" not in st.session_state:
    st.session_state.links_visible = 20
if "llm_provider" not in st.session_state:
    st.session_state.llm_provider = "openrouter"
if "openrouter_model_label" not in st.session_state:
    st.session_state.openrouter_model_label = list(OPENROUTER_MODELS.keys())[0]
if "auto_retry" not in st.session_state:
    st.session_state.auto_retry = True
if "compare_result" not in st.session_state:
    st.session_state.compare_result = None   # str: LLM comparison text
if "compare_pages_data" not in st.session_state:
    st.session_state.compare_pages_data = [] # list of scraped data dicts
if "compare_error" not in st.session_state:
    st.session_state.compare_error = None


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
            "meta": parsed.get("meta", {}),
            "raw_text": raw_text,
            "keywords": [],
            # Populated by run_analysis() after scraping
            "summary": None,
            "key_points": [],
            "topics": [],
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
        _model_keys = list(OPENROUTER_MODELS.keys())
        _saved_label = st.session_state.openrouter_model_label
        _model_index = _model_keys.index(_saved_label) if _saved_label in _model_keys else 0
        model_label = st.selectbox(
            "Model",
            options=_model_keys,
            index=_model_index,
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
    st.session_state.auto_retry = st.toggle(
        "Auto-retry on rate limit",
        value=st.session_state.auto_retry,
        help="When enabled, automatically waits and retries up to 3× on 429 rate-limit errors.",
    )

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
    st.subheader(f"📋 History ({len(st.session_state.history)})")
    if st.session_state.history:
        hist_search = st.text_input(
            "Search history",
            placeholder="Filter by title or URL…",
            label_visibility="collapsed",
            key="hist_search",
        )
        # Show newest first
        filtered_hist = list(reversed(st.session_state.history))
        if hist_search:
            q = hist_search.lower()
            filtered_hist = [
                e for e in filtered_hist
                if q in e["url"].lower() or q in e.get("title", "").lower()
            ]

        for i, entry in enumerate(filtered_hist):
            title   = entry.get("title", "Untitled")[:32]
            ts      = entry.get("ts", "")
            snippet = entry.get("snippet", "")
            is_active = (
                st.session_state.current_data is not None
                and st.session_state.current_data.get("url") == entry["url"]
            )

            with st.container():
                label = f"{'\u25b6 ' if is_active else ''}{title}"
                col_btn, col_del = st.columns([5, 1])
                with col_btn:
                    if st.button(label, key=f"hist_load_{i}", use_container_width=True,
                                 type="primary" if is_active else "secondary"):
                        st.session_state.current_data  = entry["data"]
                        st.session_state.chat_messages = []
                        st.session_state.links_visible = 20
                        st.rerun()
                with col_del:
                    if st.button("❌", key=f"hist_del_{i}", help="Remove from history"):
                        real_idx = st.session_state.history.index(entry)
                        st.session_state.history.pop(real_idx)
                        if is_active:
                            st.session_state.current_data = None
                        st.rerun()
                if ts:
                    st.caption(f"🕒 {ts}")
                if snippet:
                    st.caption(snippet[:80] + ("…" if len(snippet) > 80 else ""))

        st.markdown("")
        if st.button("🗑️ Clear All History", use_container_width=True):
            st.session_state.history = []
            st.session_state.current_data = None
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
                            auto_retry=st.session_state.auto_retry,
                        )
                        data["summary"] = analysis["summary"]
                        data["key_points"] = analysis["key_points"]
                        data["topics"] = analysis["topics"]
                        data["keywords"] = analysis["keywords"]
                    except Exception as exc:
                        st.session_state.analysis_error = str(exc)
            st.session_state.current_data = data
            st.session_state.chat_messages = []
            st.session_state.show_all_kp = False
            st.session_state.show_all_kw = False
            st.session_state.show_all_tp = False
            st.session_state.links_visible = 20
            # Add to history (avoid duplicates)
            existing_urls = [e["url"] for e in st.session_state.history]
            if data["url"] not in existing_urls:
                st.session_state.history.append({
                    "url":      data["url"],
                    "title":    data.get("title", "Untitled"),
                    "ts":       datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "snippet":  (data.get("summary") or data.get("description") or "")[:120],
                    "data":     data,
                })
            else:
                # Update existing entry in place with fresh data
                for entry in st.session_state.history:
                    if entry["url"] == data["url"]:
                        entry["title"]   = data.get("title", "Untitled")
                        entry["ts"]      = datetime.now().strftime("%Y-%m-%d %H:%M")
                        entry["snippet"] = (data.get("summary") or data.get("description") or "")[:120]
                        entry["data"]    = data
                        break
            st.success(
                f"Done! **{data['title']}** — "
                f"{len(data['paragraphs'])} paragraphs, "
                f"{len(data['links'])} links, "
                f"{len(data['images'])} images."
            )
            st.rerun()

# ── Handle Compare button ──────────────────────────────────────────────────────
if compare_clicked:
    urls = [u.strip() for u in [compare_url_1, compare_url_2, compare_url_3] if u.strip()]
    if len(urls) < 2:
        st.error("⚠️ Enter at least 2 URLs to compare.")
    else:
        provider = st.session_state.llm_provider
        openrouter_model = OPENROUTER_MODELS.get(st.session_state.openrouter_model_label)
        key_missing = (
            (provider == "openai" and not get_openai_api_key()) or
            (provider == "openrouter" and not get_openrouter_api_key())
        )
        if key_missing:
            st.session_state.compare_error = f"API key for '{provider}' is not set."
        else:
            scraped: list[dict] = []
            st.session_state.compare_error = None
            st.session_state.compare_result = None
            for url in urls:
                with st.spinner(f"Scraping {url} …"):
                    d = scrape_url(url)
                if d:
                    scraped.append(d)
                else:
                    st.session_state.compare_error = f"Failed to scrape: {url}"
                    break
            if scraped and not st.session_state.compare_error:
                st.session_state.compare_pages_data = scraped
                label = st.session_state.openrouter_model_label if provider == "openrouter" else provider
                with st.spinner(f"Comparing with {label} …"):
                    try:
                        st.session_state.compare_result = compare_pages(
                            scraped,
                            provider=provider,
                            openrouter_model=openrouter_model,
                            auto_retry=st.session_state.auto_retry,
                        )
                    except Exception as exc:
                        st.session_state.compare_error = str(exc)
        st.rerun()

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
                st.caption("_No significant keywords found on this page._")

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

        # Export buttons
        st.markdown("---")
        ec1, ec2, _ = st.columns([1, 1, 4])
        _slug = (data.get("title") or "analysis").replace(" ", "_")[:40]
        with ec1:
            try:
                pdf_bytes = to_pdf(data)
                st.download_button(
                    "📄 Export PDF",
                    data=pdf_bytes,
                    file_name=f"{_slug}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as _e:
                st.button("📄 Export PDF", disabled=True, help=f"PDF error: {_e}")
        with ec2:
            md_str = to_markdown(data)
            st.download_button(
                "📝 Export Markdown",
                data=md_str,
                file_name=f"{_slug}.md",
                mime="text/markdown",
                use_container_width=True,
            )

    else:
        show_placeholder(
            "Summary",
            "Analyze a URL to see the AI-generated summary, key points, topics, and keywords here.",
        )

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
                            st.session_state.chat_messages,
                            provider=provider,
                            openrouter_model=openrouter_model,
                            auto_retry=st.session_state.auto_retry,
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
        links  = data.get("links", [])
        images = data.get("images", [])
        headings = data.get("headings", [])
        meta     = data.get("meta", {})

        import pandas as pd

        # ── Stats row ─────────────────────────────────────────────────────────
        n_internal = sum(1 for l in links if l.get("type") == "internal")
        n_external = len(links) - n_internal
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🔗 Total Links",    len(links))
        m2.metric("🏠 Internal",       n_internal)
        m3.metric("🌐 External",       n_external)
        m4.metric("🖼️ Images",         len(images))
        st.markdown("---")

        # ── Links section ─────────────────────────────────────────────────────
        st.markdown("#### 🔗 Links")

        col_filter, col_search = st.columns([1, 2])
        with col_filter:
            filter_type = st.radio(
                "Type", ["All", "Internal", "External"],
                horizontal=True, key="link_filter",
            )
        with col_search:
            search_q = st.text_input(
                "Search", placeholder="Filter by URL or link text…",
                label_visibility="collapsed", key="link_search",
            )

        if links:
            df_links = pd.DataFrame(links)          # href, text, type
            if filter_type != "All":
                df_links = df_links[df_links["type"] == filter_type.lower()]
            if search_q:
                mask = (
                    df_links["href"].str.contains(search_q, case=False, na=False) |
                    df_links["text"].str.contains(search_q, case=False, na=False)
                )
                df_links = df_links[mask]

            total_filtered = len(df_links)
            # Reset visible count when filters change
            visible_n = min(st.session_state.links_visible, total_filtered)
            df_page = df_links.iloc[:visible_n]

            # Make URLs clickable
            df_display = df_page.copy()
            df_display["href"] = df_display["href"].apply(
                lambda u: f'<a href="{u}" target="_blank">{u}</a>'
            )
            df_display.columns = ["URL", "Link Text", "Type"]
            st.write(
                df_display.to_html(escape=False, index=False),
                unsafe_allow_html=True,
            )

            # ── Show more / show less controls ────────────────────────────────
            cap_col, btn_col = st.columns([3, 1])
            with cap_col:
                st.caption(f"Showing {visible_n} of {total_filtered} links")
            with btn_col:
                if visible_n < total_filtered:
                    if st.button(f"Show 20 more ▼", key="links_more"):
                        st.session_state.links_visible += 20
                        st.rerun()
                elif total_filtered > 20:
                    if st.button("Show less ▲", key="links_less"):
                        st.session_state.links_visible = 20
                        st.rerun()
        else:
            st.caption("_No links found on this page._")

        st.markdown("---")

        # ── Images section ────────────────────────────────────────────────────
        st.markdown(f"#### 🖼️ Images — {len(images)} found")
        if images:
            view_mode = st.radio(
                "View", ["Grid", "Table"], horizontal=True, key="img_view"
            )
            if view_mode == "Grid":
                cols_per_row = 4
                for row_start in range(0, len(images), cols_per_row):
                    row_imgs = images[row_start : row_start + cols_per_row]
                    cols = st.columns(cols_per_row)
                    for col, img in zip(cols, row_imgs):
                        with col:
                            try:
                                st.image(img["src"], caption=img["alt"] or "—", use_container_width=True)
                            except Exception:
                                st.markdown(
                                    f'<a href="{img["src"]}" target="_blank">🔗 View image</a>',
                                    unsafe_allow_html=True,
                                )
                                if img["alt"]:
                                    st.caption(img["alt"])
            else:
                df_img = pd.DataFrame(images)
                df_img["src"] = df_img["src"].apply(
                    lambda u: f'<a href="{u}" target="_blank">{u}</a>'
                )
                df_img.columns = ["Image URL", "Alt Text"]
                st.write(df_img.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.caption("_No images found on this page._")

        st.markdown("---")

        # ── Page structure (headings outline) ─────────────────────────────────
        with st.expander(f"📑 Page Structure — {len(headings)} headings", expanded=False):
            if headings:
                for h in headings:
                    st.markdown(f"- {h}")
            else:
                st.caption("_No headings found._")

        # ── Meta tags ─────────────────────────────────────────────────────────
        with st.expander(f"🏷️ Meta Tags — {len(meta)} found", expanded=False):
            if meta:
                df_meta = pd.DataFrame(meta.items(), columns=["Property", "Value"])
                st.dataframe(df_meta, use_container_width=True, hide_index=True)
            else:
                st.caption("_No meta tags found._")

    else:
        show_placeholder(
            "Data",
            "Analyze a URL to see all links, images, page structure, and meta tags extracted from the page.",
        )

# ── Compare Tab ───────────────────────────────────────────────────────────────
with tab_compare:
    st.markdown("#### ⚖️ Multi-URL Comparison")
    st.caption("Enter 2–3 URLs in the sidebar and click **Compare**.")
    st.markdown("---")

    if st.session_state.compare_error:
        st.error(f"🚨 {st.session_state.compare_error}")

    if st.session_state.compare_result:
        pages_data = st.session_state.compare_pages_data

        # ── Per-page stat cards ──────────────────────────────────────────
        cols = st.columns(len(pages_data))
        for col, page in zip(cols, pages_data):
            with col:
                st.markdown(f"**{page.get('title', 'Untitled')[:50]}**")
                st.caption(page.get('url', '')[:60])
                st.markdown(
                    f"- 📖 {len(page.get('paragraphs', []))} paragraphs  \n"
                    f"- 🔗 {len(page.get('links', []))} links  \n"
                    f"- 🖼️ {len(page.get('images', []))} images"
                )
        st.markdown("---")

        # ── AI comparison report ────────────────────────────────────────────
        st.markdown("#### 🧠 AI Comparison Report")
        st.write(st.session_state.compare_result)
        st.markdown("---")

        # ── Export comparison ──────────────────────────────────────────────
        md_lines = ["# Comparison Report\n"]
        for page in pages_data:
            md_lines.append(f"- **{page.get('title', 'Untitled')}** — {page.get('url', '')}")
        md_lines.append(f"\n---\n\n{st.session_state.compare_result}")
        st.download_button(
            "📝 Export Comparison as Markdown",
            data="\n".join(md_lines),
            file_name="comparison.md",
            mime="text/markdown",
        )

    elif not st.session_state.compare_error:
        show_placeholder(
            "Compare",
            "Enter 2–3 URLs in the sidebar and click **Compare** to see an AI side-by-side comparison.",
        )
