# Website Descriptor - Project Plan

> **Goal:** Build a web application that takes a website URL as input, scrapes and cleans its content, and uses an LLM to generate rich summaries, insights, and analysis - all through an intuitive Streamlit UI.
>
> **Status: Complete - v1.0.0**

---

## 1. Tech Stack - As Built

| Layer | Planned | Actually Used |
|-------|---------|---------------|
| **UI** | Streamlit | Streamlit |
| **Scraping** | requests + BeautifulSoup4 + Playwright fallback | requests + Session + urllib3.Retry + BeautifulSoup4 + lxml (Playwright not needed) |
| **LLM** | OpenAI only | **3 providers:** OpenAI, Ollama (local), OpenRouter |
| **Keyword Extraction** | Not specified | **LLM-based** (4th prompt call) - evaluated TF-IDF, YAKE, spaCy before settling here |
| **PDF Export** | Planned | fpdf2 with Unicode sanitizer + token-wrapping for long URLs |
| **Language** | Python 3.10+ | Python 3.14 |
| **Env Management** | python-dotenv | python-dotenv with `override=True` |

---

## 2. Core Features - As Built

### 2.1 Website Scraping
- URL validated and normalised (auto-prepends `https://`) before any request
- Blocked-domain list: medium.com, Twitter/X, Facebook, Instagram, LinkedIn, Netflix, Cloudflare
- `requests.Session` with `urllib3.Retry` (3 retries, backoff on 429/5xx)
- Realistic browser headers (User-Agent, Accept-Language, Accept-Encoding, DNT)
- Encoding detection: respects Content-Type charset, falls back to `apparent_encoding`
- BeautifulSoup4 + lxml parser; strips noise tags (script, style, nav, footer, aside, form, svg...)
- Extracts: title, meta description, headings (h1-h4), paragraphs (>40 chars),
  links (internal/external, deduplicated), images (src + alt, deduplicated), all meta tags
- Empty-content guard: shows warning if page returns <50 chars of usable text

### 2.2 Content Cleaning
- Normalises whitespace, collapses newlines, strips zero-width and non-printable chars
- `build_content()` assembles structured text: TITLE -> DESCRIPTION -> HEADINGS -> CONTENT
- `chunk_text()` splits oversized content to fit LLM context window (MAX_CONTENT_CHARS = 12000)

### 2.3 LLM-Powered Analysis (4 prompts per page)
- **Summary** - 3-5 sentence concise overview
- **Key Points** - JSON array of 5-8 bullet points
- **Topics** - JSON array of 3-6 short topic labels
- **Keywords** - JSON array of 10-20 domain-specific terms/keyphrases (LLM-extracted)
- `_chat_with_retry()` - auto-sleeps and retries up to 3x on 429 rate-limit errors
- Progress callback pattern: live `st.progress` bar updates at each of the 4 steps
- **Auto-retry toggle** in sidebar - turn off for models that don't need it

---

## 3. Additional Features - As Built

| Phase | Feature | What Was Built |
|-------|---------|----------------|
| 4 | **Conversational Q&A** | Full chat with persistent history; `qa_messages()` sends entire conversation + page content as system prompt; Clear button; API key guard per message |
| 5 | **Keyword Extraction** | Evaluated TF-IDF (custom stdlib), YAKE, spaCy noun chunks, LLM prompt. Settled on **LLM prompt** - 4th analysis call alongside summary/topics/key-points |
| 6 | **Link & Image Extraction** | 4 metric cards (total/internal/external/images); links table with type filter + live search + show-more pagination (20 at a time); images in Grid (4-col thumbnails) or Table view; Page Structure expander; Meta Tags expander |
| 7 | **Export** | `to_markdown()` - structured .md with all sections + links table; `to_pdf()` - fpdf2 with custom header/footer, Unicode sanitizer (`_s()`), long-token wrapping (`_wrap()`) |
| 8 | **Multi-URL Comparison** | Up to 3 URLs; per-page stat cards; AI comparison report; export as Markdown |
| 9 | **Session History** | Count in header; search/filter box; newest-first; active page highlighted with primary button; per-entry delete (X); timestamps + snippet; re-analyses update entry in-place |
| 10 | **Polish & Edge Cases** | URL pre-validation + auto https://; expanded blocked-domain list; empty-content guard; 4-step progress bar during analysis; `st.toast` success notification; `show_scrape_stats()` inline banner; styled placeholder cards; Help & About expander; app footer |

---

## 4. LLM Providers

Three providers selectable from the sidebar radio:

| Provider | Env var | Notes |
|----------|---------|-------|
| OpenRouter (default) | `OPENROUTER_API_KEY` | Free models available (`:free` suffix). 429 auto-retry built in. |
| Ollama (local) | none | Runs offline. Default model: `gemma3:270m`. Requires `ollama serve`. |
| OpenAI | `OPENAI_API_KEY` | Paid. Default model: `gpt-4o-mini`. |

---

## 5. Project Structure - As Built

```
website-descriptor/
|-- app.py                  # Streamlit entry point + all UI orchestration
|-- requirements.txt        # All Python dependencies
|-- .env.example            # Template for API keys
|-- README.md               # Setup and usage guide
|-- PLAN.md                 # This file
|-- context.md              # Dev handoff/session notes
|
|-- scraper/
|   |-- fetcher.py          # validate_url(), fetch_html() + Session + Retry + blocked domains
|   |-- parser.py           # BeautifulSoup4 extraction: title, headings, paragraphs, links, images, meta
|   +-- cleaner.py          # clean_text(), build_content()
|
|-- analyzer/
|   |-- llm_client.py       # Multi-provider OpenAI-SDK client (OpenAI / Ollama / OpenRouter)
|   |-- prompts.py          # summary, key_points, topics, keywords, qa, comparison prompt builders
|   +-- analysis.py         # _chat_with_retry(), analyse_page(), answer_question(), compare_pages()
|
|-- ui/
|   |-- components.py       # show_placeholder(), show_api_key_warning(), show_scrape_stats()
|   +-- export.py           # to_markdown(), to_pdf() with Unicode sanitizer
|
|-- utils/
|   |-- config.py           # Env loading, APP_TITLE / APP_VERSION / APP_ICON, provider configs
|   +-- text_utils.py       # chunk_text(), extract_keywords() (spaCy, kept as optional fallback)
|
+-- docs/
    +-- keyword-extraction-methods.md  # Research: TF-IDF vs YAKE vs KeyBERT vs spaCy vs LLM
```

---

## 6. Known Decisions and Trade-offs

| Decision | Reason |
|----------|--------|
| LLM keyword extraction over spaCy/YAKE | Better domain-specific results; one extra API call is acceptable |
| `load_dotenv(override=True)` | Prevents shell env vars silently shadowing `.env` values |
| Progress callback (not `st.status`) | Works correctly across Streamlit reruns without state issues |
| fpdf2 Unicode sanitizer + token wrapper | Helvetica is Latin-1 only; safer than requiring font files |
| No Playwright in final build | Static `requests` sufficient for all tested sites |
| `requests.Session` recreated per call | Avoids connection pool state leaking across unrelated domains |
| `validate_url()` exported from fetcher | Lets app.py pre-check before spinning up scrape UI |
