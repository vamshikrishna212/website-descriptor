# Website Descriptor — Project Plan

> **Goal:** Build a web application that takes a website URL as input, scrapes and cleans its content, and uses an LLM to generate rich summaries, insights, and analysis — all through an intuitive Streamlit UI.

---

## 1. Tech Stack

| Layer | Technology |
|-------|-----------|
| **UI** | Streamlit |
| **Scraping** | `requests` + `BeautifulSoup4` (static sites), `Playwright` (JS-rendered sites) |
| **LLM** | OpenAI API (`gpt-4o-mini` / `gpt-4o`) via `openai` SDK |
| **Language** | Python 3.10+ |
| **Env Management** | `python-dotenv` for API keys |

---

## 2. Core Features

### 2.1 Website Scraping
- Accept a URL from the user.
- Fetch the page HTML using `requests` (with fallback to `Playwright` for JavaScript-heavy sites).
- Parse and extract meaningful content (title, headings, paragraphs, links, images, meta tags).
- Strip ads, navigation bars, footers, scripts, and other boilerplate.

### 2.2 Content Cleaning & Preprocessing
- Remove HTML tags, extra whitespace, and special characters.
- Detect and handle encoding issues.
- Chunk long content to fit within LLM token limits.
- Structure the cleaned text into sections (headings → body mapping).

### 2.3 LLM-Powered Analysis
- **Summary:** Generate a concise summary of the entire page.
- **Key Points:** Extract bullet-point highlights.
- **Topic Detection:** Identify the main topics/themes of the page.

---

## 3. Additional Features

| Feature | Description |
|---------|-------------|
| **Conversational Q&A** | Chat interface where users can ask follow-up questions about the scraped content with full conversation history. |
| **Multi-URL Comparison** | Scrape 2+ URLs and generate a side-by-side comparison summary. |
| **Export Results** | Download the analysis as PDF or Markdown. |
| **Keyword Extraction** | Pull out the most important keywords and phrases. |
| **Link Extractor** | List all internal and external links found on the page. |
| **Image Listing** | Display all images found with their alt text. |
| **History / Session Log** | Keep a sidebar log of previously analyzed URLs in the session. |

---

## 4. Project Structure

```
website-descriptor/
├── app.py                  # Streamlit entry point
├── requirements.txt        # Python dependencies
├── .env.example            # Template for API keys
├── README.md               # Project overview and setup guide
├── PLAN.md                 # This file
│
├── scraper/
│   ├── __init__.py
│   ├── fetcher.py          # URL fetching (requests + Playwright fallback)
│   ├── parser.py           # HTML parsing and content extraction
│   └── cleaner.py          # Text cleaning and preprocessing
│
├── analyzer/
│   ├── __init__.py
│   ├── llm_client.py       # OpenAI API wrapper
│   ├── prompts.py          # Prompt templates for each analysis type
│   └── analysis.py         # Orchestrates different analysis tasks
│
├── ui/
│   ├── __init__.py
│   ├── components.py       # Reusable Streamlit UI components
│   └── export.py           # PDF / Markdown export helpers
│
└── utils/
    ├── __init__.py
    ├── text_utils.py        # Chunking, keyword extraction helpers
    └── config.py            # App configuration and env loading
```

---

## 5. Streamlit UI Layout

```
┌──────────────────────────────────────────────────────┐
│  🌐 Website Descriptor                              │
├──────────────┬───────────────────────────────────────┤
│              │                                       │
│  Sidebar     │   Main Area (Tabs)                    │
│  ────────    │   ─────────────────                   │
│              │                                       │
│  URL Input   │   📝 Summary  │ 💬 Chat  │ 🔗 Data   │
│  [________]  │   ──────────────────────────────────  │
│              │                                       │
│  [Analyze]   │   (Tab content renders here)          │
│              │                                       │
│  ── Options ─│   Summary Tab:                        │
│  ☐ Summary   │     • Page summary                    │
│  ☐ Key Pts   │     • Key points                      │
│  ☐ Keywords  │     • Keywords                        │
│              │                                       │
│  ── History ─│   Chat Tab:                           │
│  • url1.com  │     • Conversation with LLM           │
│  • url2.com  │     • Ask anything about the page     │
│              │                                       │
│  ── Compare ─│   Data Tab:                           │
│  [Add URLs]  │     • Links list                      │
│  [Compare]   │     • Images list                     │
│              │                                       │
│              │   ┌─────────────────────────────────┐ │
│              │   │  Export: [📄 PDF] [📝 Markdown] │ │
│              │   └─────────────────────────────────┘ │
└──────────────┴───────────────────────────────────────┘
```

---

## 6. Implementation Phases

> **Principle:** UI first — every phase starts by building/updating the Streamlit interface so progress is visible immediately, then wires in the backend logic.

---

### Phase 1 — Project Setup & UI Shell ✅
> Lay the groundwork: project structure, dependencies, and a working Streamlit app with placeholder screens.

- [x] Initialize project folder structure (all packages, `__init__.py` files).
- [x] Create `requirements.txt` and `.env.example`.
- [x] Build `app.py` with Streamlit page config, sidebar layout, and tab structure.
- [x] Add URL input field in sidebar and placeholder content in each tab.
- [x] Set up `utils/config.py` for env loading.
- [x] Verify the app launches and all navigation works with dummy data.

**Deliverable:** A running Streamlit app with full navigation, tabs, and placeholder text.

---

### Phase 2 — Website Scraping & Raw Content Display ✅
> Scrape a URL and display the raw cleaned content in the UI.

- [x] Implement `scraper/fetcher.py` — fetch HTML via `requests` with proper headers and error handling.
- [x] Implement `scraper/parser.py` — extract title, headings, paragraphs, links, images, meta tags using BeautifulSoup.
- [x] Implement `scraper/cleaner.py` — strip boilerplate, clean whitespace, handle encoding.
- [x] Update UI: wire the **Analyze** button to trigger scraping.
- [x] Display the cleaned raw content in a "Raw Content" expander in the Summary tab.
- [x] Add loading spinner and error messages for failed URLs.

**Deliverable:** Enter a URL → click Analyze → see cleaned text content in the app.

---

### Phase 3 — LLM Integration (Summary & Key Points) ✅
> Connect to OpenAI and generate the core analysis.

- [x] Implement `analyzer/llm_client.py` — OpenAI API wrapper with error handling and token management.
- [x] Implement `analyzer/prompts.py` — prompt templates for summary, key points, and topic detection.
- [x] Implement `analyzer/analysis.py` — orchestrator that runs prompts against scraped content.
- [x] Implement `utils/text_utils.py` — content chunking for large pages.
- [x] Update UI Summary tab: display generated summary, key points, and detected topics.
- [x] Add loading states while LLM processes.

**Deliverable:** Enter a URL → get a full AI-generated summary with key points and topics.

---

### Phase 4 — Conversational Q&A
> Let users ask follow-up questions about the scraped content in a chat interface.

- [ ] Add a Chat tab in the UI using `st.chat_message` and `st.chat_input`.
- [ ] Maintain conversation history in `st.session_state`.
- [ ] Build a Q&A prompt template that includes the scraped content as context + conversation history.
- [ ] Stream LLM responses into the chat interface.
- [ ] Handle edge cases: no content scraped yet, very long conversations (truncate older messages).

**Deliverable:** After scraping a URL, users can have a multi-turn conversation asking questions about the page content.

---

### Phase 5 — Keyword Extraction
> Extract and display the most important keywords and phrases from the page.

- [ ] Implement keyword extraction logic in `utils/text_utils.py` (TF-based or LLM-assisted).
- [ ] Add a Keywords section in the Summary tab (display as styled tags/chips).
- [ ] Allow clicking a keyword to search it within the scraped content (highlight occurrences).

**Deliverable:** Keywords appear as visual tags after analysis, giving a quick overview of the page topics.

---

### Phase 6 — Link Extractor & Image Listing
> Show all links and images found on the page in a structured format.

- [ ] Update `scraper/parser.py` to collect all links (href, text, internal/external flag).
- [ ] Update `scraper/parser.py` to collect all images (src, alt text, dimensions if available).
- [ ] Build the Data tab UI: links table with columns (URL, text, type) and image gallery with alt text.
- [ ] Add filtering (internal vs external links) and search within links.

**Deliverable:** Data tab shows a filterable links table and an image gallery with metadata.

---

### Phase 7 — Export Results
> Let users download the full analysis as PDF or Markdown.

- [ ] Implement `ui/export.py` — format analysis results into Markdown string.
- [ ] Implement PDF generation using `fpdf2` (summary, key points, keywords, links).
- [ ] Add export buttons in the UI (bottom of Summary tab).
- [ ] Use `st.download_button` for both PDF and Markdown downloads.

**Deliverable:** Users can export the complete analysis to PDF or Markdown with one click.

---

### Phase 8 — Multi-URL Comparison
> Compare content from multiple websites side by side.

- [ ] Add a "Compare" section in the sidebar with inputs for 2–3 URLs.
- [ ] Scrape and analyze all URLs in parallel.
- [ ] Build a comparison prompt template that highlights similarities and differences.
- [ ] Display comparison results in a dedicated view (side-by-side columns or a comparison table).

**Deliverable:** Users can enter multiple URLs and get an AI-generated comparison of their content.

---

### Phase 9 — Session History
> Track all analyzed URLs in the current session for quick re-access.

- [ ] Store each analyzed URL + results in `st.session_state` history list.
- [ ] Display history in the sidebar with clickable entries.
- [ ] Clicking a history entry reloads its cached results (no re-scraping needed).
- [ ] Add a "Clear History" button.

**Deliverable:** Sidebar shows a log of all analyzed URLs; users can click to revisit past results instantly.

---

### Phase 10 — Polish & Edge Cases
> Harden the app and handle real-world scenarios.

- [ ] Handle timeouts, blocked sites (403/429), and redirect chains gracefully.
- [ ] Add Playwright fallback for JavaScript-rendered pages.
- [ ] Rate-limit LLM calls and show usage feedback.
- [ ] Add input validation (URL format, reachability check).
- [ ] Responsive UI tweaks and final styling.
- [ ] Update README with setup instructions, usage guide, and screenshots.

**Deliverable:** A production-ready, robust application that handles edge cases gracefully.

---

## 7. Phase Summary

| Phase | Feature | Key Outcome |
|-------|---------|-------------|
| 1 | Project Setup & UI Shell | Running app with full navigation |
| 2 | Website Scraping | URL → cleaned text in UI |
| 3 | LLM Summary & Key Points | AI-generated analysis |
| 4 | Conversational Q&A | Multi-turn chat about page content |
| 5 | Keyword Extraction | Visual keyword tags |
| 6 | Links & Images | Structured data extraction |
| 7 | Export Results | PDF & Markdown downloads |
| 8 | Multi-URL Comparison | Side-by-side website comparison |
| 9 | Session History | Quick re-access to past analyses |
| 10 | Polish & Edge Cases | Production-ready robustness |

---

## 8. Key Dependencies

```
streamlit
requests
beautifulsoup4
openai
python-dotenv
playwright
fpdf2
```

---

## 9. Running the App

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# Launch
streamlit run app.py
```
