# Keyword Extraction Methods

> Reference notes for choosing a keyword extraction approach in the Website Descriptor project.

---

## Current Implementation

**TF-IDF-ish (custom, stdlib only)** — `utils/text_utils.py`

- Tokenizes with regex, filters ~130 stopwords
- Scores unigrams by frequency; bigrams appearing 2+ times get a 1.8× boost
- Deduplicates: if a bigram covers a word, the bare unigram is skipped
- Returns up to 20 keywords, no dependencies
- Weakness: treats words statistically only, misses semantic meaning

---

## Method Comparisons

| Method | Quality | Speed | Dependencies | Phrases |
|---|---|---|---|---|
| Current (TF-IDF-ish) | ⭐⭐ | ⚡ instant | none | basic bigrams |
| RAKE | ⭐⭐⭐ | ⚡ fast | `rake-nltk` | ✅ good |
| YAKE | ⭐⭐⭐⭐ | ⚡ fast | `yake` | ✅ good |
| KeyBERT | ⭐⭐⭐⭐⭐ | 🐢 slow (1st run) | `keybert` + model | ✅ best |
| spaCy | ⭐⭐⭐⭐ | ✅ fast after load | `spacy` + model | ✅ good |
| LLM prompt | ⭐⭐⭐⭐⭐ | 🌐 API latency | none (already wired) | ✅ best |

---

## YAKE (Yet Another Keyword Extractor)

**Install:** `pip install yake`

Unsupervised, statistical, language-agnostic. Scores candidates using 5 features — **lower score = more important**.

### Feature 1 — TCase (Casing)
Words appearing in Title Case or ALL CAPS in the original text score higher — likely proper nouns or important terms.
```
"Machine Learning" → high TCase score
"the"             → low TCase score
```

### Feature 2 — TPosition (Position)
Words appearing earlier in the document score higher. Authors front-load important concepts in titles, first paragraphs, and headings.
```
word at sentence 1  → score ≈ log(2)  → low penalty
word at sentence 50 → score ≈ log(51) → high penalty
```

### Feature 3 — TFreq (Frequency)
Raw term frequency normalized against the **median frequency** of all words — prevents common words that slip through stopword filters from dominating.

### Feature 4 — TRel (Relatedness to Context)
Measures how many different words appear alongside the candidate. A keyword surrounded by many varied words is more contextually central.

### Feature 5 — TSentences (Sentence Spread)
How many different sentences the word appears in. A word spread across many sentences is a recurring theme.

### Final Score Formula

$$S(w) = \frac{TCase \times TPosition \times TFreq}{TRel \times (1 + TSentences)}$$

Phrases are formed by combining adjacent words and multiplying their individual scores.

### Usage example
```python
import yake

kw_extractor = yake.KeywordExtractor(lan="en", n=2, top=20)
keywords = kw_extractor.extract_keywords(text)
# returns: [("machine learning", 0.013), ("neural network", 0.021), ...]
# lower score = more important
```

---

## KeyBERT

**Install:** `pip install keybert sentence-transformers`  
**Model download:** ~80MB (`all-MiniLM-L6-v2`) to ~500MB (larger models)

Uses sentence-transformer embeddings to find words/phrases semantically closest to the document's overall meaning.

### Step 1 — Embed the whole document
The page text is fed into a sentence-transformer model, producing a 384-dimensional vector representing the document's meaning.
```
"Article about neural networks..." → [0.23, -0.11, 0.87, ...]
```

### Step 2 — Generate candidates
N-gram candidates (1, 2, or 3-word phrases) are extracted, stopwords filtered:
```
candidates = ["neural network", "deep learning", "gradient descent", ...]
```

### Step 3 — Embed each candidate
Each candidate phrase gets its own embedding vector via the same model.

### Step 4 — Cosine similarity
Each candidate vector is compared to the document vector:

$$\text{similarity} = \frac{\vec{candidate} \cdot \vec{document}}{|\vec{candidate}| \cdot |\vec{document}|}$$

Candidates closest in vector space = most representative keywords.

### Step 5 — MMR (Maximal Marginal Relevance)
Avoids returning 10 synonyms. Iteratively picks the next keyword that is similar to the document but **dissimilar to already-chosen keywords**:
```
Without MMR: ["AI", "artificial intelligence", "AI system", "AI model", ...]
With MMR:    ["artificial intelligence", "neural network", "training data", ...]
```

### Usage example
```python
from keybert import KeyBERT

kw_model = KeyBERT()  # downloads model on first run
keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), top_n=20, use_mmr=True)
# returns: [("machine learning", 0.82), ("neural network", 0.79), ...]
```

---

## spaCy + Noun Chunks

**Install:** `pip install spacy` then `python -m spacy download en_core_web_sm`  
**Model size:** ~15MB (`en_core_web_sm`)

Uses a trained neural pipeline to extract grammatically valid noun phrases.

### Stage 1 — Tokenization
Text split into tokens respecting contractions, punctuation, hyphens:
```
"climate-change policy" → ["climate-change", "policy"]
```

### Stage 2 — POS Tagging
Each token gets a grammatical label via a bidirectional CNN trained on annotated corpora:
```
"The"      → DET
"climate"  → NOUN
"change"   → NOUN
"policy"   → NOUN
"reduces"  → VERB
```

### Stage 3 — Dependency Parsing
A parser builds a dependency tree — which words modify which:
```
policy ← change ← climate
  ↑
reduces → emissions
```

### Noun Chunk Extraction
spaCy walks the dependency tree and collects noun phrases (noun head + left-side modifiers):
```python
for chunk in doc.noun_chunks:
    print(chunk.text)
# → "climate change policy"
# → "carbon emissions"
# → "renewable energy sources"
```

Produces linguistically grounded phrases — won't produce `"the reducing"` or `"policy reduces"`.

### Usage example
```python
import spacy
from collections import Counter

nlp = spacy.load("en_core_web_sm")
doc = nlp(text)
chunks = [chunk.text.lower() for chunk in doc.noun_chunks if len(chunk.text) > 3]
keywords = [kw for kw, _ in Counter(chunks).most_common(20)]
```

---

## Recommendation

| Goal | Best choice |
|---|---|
| No extra dependencies, good enough | Current implementation |
| Easy quality upgrade, one pip install | **YAKE** |
| Best semantic understanding, okay with model download | **KeyBERT** |
| Grammatically accurate phrases, already using spaCy | **spaCy** |
| Already using LLM, want best results | **LLM prompt** (extra `keywords_messages()` call) |
