# ════════════════════════════════════════════════════════════════════════════════
# EXAMHELP AI v5.0 — COMPLETE REBUILD MASTER PROMPT FOR GEMINI
# Written by: Claude (Brain) | Executed by: Gemini 2.5 Pro (Hands)
# Scope: Full Production-Grade Streamlit App — Zero Stubs, Zero TODOs
# ════════════════════════════════════════════════════════════════════════════════

---

## ABSOLUTE PRIME DIRECTIVES — READ BEFORE TOUCHING ANY FILE

You are an elite full-stack Python/Streamlit engineer rebuilding **ExamHelp AI v5.0**
from an existing v4.0 codebase. You have been given the complete source tree.
Your job is NOT to write summaries, plans, or outlines. Your job is to write
**working, complete, copy-paste-ready Python code** for every file listed below.

### Prime Rules (Violating even one = task failure):

**PRIME-1:** Every single function must be 100% implemented. Zero placeholders.
Zero `pass` statements (unless in an abstract base class). Zero `# TODO` comments.
Zero `raise NotImplementedError`. Every function body must do real work.

**PRIME-2:** Every file you produce must be a COMPLETE file — not a diff, not a
partial snippet. Produce the FULL file content from the very first import line
to the very last line. If a file is 800 lines, write all 800 lines.

**PRIME-3:** All APIs used MUST be free-tier accessible with no credit card
required. Every API endpoint, every library, every service must be genuinely
free and functional as of 2025. No paid services disguised as free.

**PRIME-4:** Never break backward compatibility. Functions that already exist in
`utils/ai_engine.py::generate()`, `generate_stream()`, and `json_generate()`
must keep their existing signatures. You may ADD parameters with defaults.
You must NOT remove or rename existing parameters.

**PRIME-5:** The entire app runs on `streamlit run app.py`. Nothing should
require manual daemon startup, Redis, Celery, Docker, or external databases.
All state lives in `st.session_state` or Python module-level singletons.

**PRIME-6:** Every external API call (not Gemini) must have:
- A try/except around it
- A human-readable fallback message
- A session_state cache with TTL

**PRIME-7:** Read this ENTIRE document before writing a single line. Then execute
it sequentially, file by file, section by section.

---

## SECTION A — PROJECT ARCHITECTURE OVERVIEW

### Stack (Do Not Change):
- **Language:** Python 3.12
- **UI Framework:** Streamlit (latest stable)
- **Primary AI:** Google Gemini 2.5 Flash via REST API (free tier)
- **Key Rotation:** `utils/omnikey_engine.py` — 9-key OmniKeyEngine singleton
- **Prompt Registry:** `utils/prompts.py` — ENGINE_PROMPTS dict
- **UI Style:** Glassmorphism CSS, Plotly charts, Streamlit widgets

### File Structure (Complete):
```
app.py                          ← Main entry point + navigation
advanced_features.py            ← Secondary feature renderers
new_features.py                 ← Elite expert engines UI
utils/
  ai_engine.py                  ← High-level AI orchestration
  omnikey_engine.py             ← 9-key rotation engine
  prompts.py                    ← All system prompts + configs
  flashcard_engine.py           ← Flashcard generation + SM-2
  quiz_engine.py                ← Quiz generation + adaptive mode
  essay_engine.py               ← Essay writer + outline + improve
  debugger_engine.py            ← Code debugger + security audit
  interview_engine.py           ← Interview coach + mock mode
  research_engine.py            ← Research synthesis + gaps
  citation_engine.py            ← 7-style citations + BibTeX export
  pdf_handler.py                ← PDF extraction + chunking
  web_handler.py                ← Web scraping + robots.txt
  youtube_handler.py            ← Transcript + timestamp Q&A
  notes_engine.py               ← Smart notes + tagging + linking
  regex_engine.py               ← Regex tester + AI explainer
  vit_engine.py                 ← VIT CGPA + attendance + planner
  security_utils.py             ← Key masking + input sanitization
  analytics.py                  ← Study analytics + charts
  presentation_engine.py        ← Slide deck generator
  shopping_engine.py            ← Product analysis
  language_engine.py            ← Translation + grammar
  flashcard_engine.py           ← Already listed above
  omnikey_engine.py             ← Already listed above
  secret_manager.py             ← Key loading from st.secrets
  gemini_key_manager.py         ← Key validation utilities
  key_manager.py                ← Legacy key compat layer
  ocr_handler.py                ← Image OCR via Gemini Vision
  file_engine.py                ← File upload + type detection
  context_focus_engine.py       ← Focus mode + distraction block
  study_generator.py            ← Study plan generator
  study_tools.py                ← Study helper utilities
  app_controller.py             ← App-wide controller logic
  chat_powerup.py               ← Chat enhancement features
  graph_engine.py               ← Mind map + Mermaid generation
  query_engine.py               ← Smart query processing
  solver_engine.py              ← Problem solving engine
  code_converter_engine.py      ← Code language converter
  contest_engine.py             ← Competitive programming helper
  personas.py                   ← 30+ AI persona definitions
  groq_client.py                ← Groq Whisper client
  key_protector.py              ← Key obfuscation utils
ai/
  api_manager.py                ← API routing + model selection
  gemini_client.py              ← Raw Gemini REST client
  image_engine.py               ← Image analysis via Gemini Vision
  reasoning_engine.py           ← Chain-of-thought reasoning
  api_helper.py                 ← API utility functions
  plugin_registry.py            ← Plugin system registry
memory/
  vector_store.py               ← In-memory vector store for RAG
voice/
  input.py                      ← Audio recording + transcription
chat/
  feedback.py                   ← Chat feedback collection
  share.py                      ← Chat sharing functionality
ui/
  doc_editor.py                 ← Document editor UI
  story_builder.py              ← Story creation UI
```

---

## SECTION B — FREE APIs CATALOGUE
### (Every API listed here is free, no credit card needed, use exactly these)

#### B.1 — AI & Language APIs (All Free Tier)

**Google Gemini API (PRIMARY — ALREADY INTEGRATED)**
- Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`
- Auth: `?key=YOUR_API_KEY` query param
- Free tier: 15 RPM, 1M TPM, 1500 RPD per key
- Keys: Loaded from `st.secrets["GEMINI_API_KEY_1"]` through `["GEMINI_API_KEY_9"]`
- Get keys: https://aistudio.google.com/app/apikey (free Google account)

**Groq API (FOR WHISPER VOICE TRANSCRIPTION)**
- Endpoint: `https://api.groq.com/openai/v1/audio/transcriptions`
- Auth: Bearer token header
- Model: `whisper-large-v3`
- Free tier: Generous free tier with rate limits
- Key: Loaded from `st.secrets["GROQ_API_KEY"]`
- Get key: https://console.groq.com (free signup)

#### B.2 — Data & Information APIs (All Genuinely Free)

**NewsAPI.org (FOR NEWS HUB FEATURE)**
- Endpoint: `https://newsapi.org/v2/everything` and `/v2/top-headlines`
- Auth: `?apiKey=YOUR_KEY` param
- Free tier: 100 requests/day, developer plan
- Key: `st.secrets["NEWS_API_KEY"]`
- Get key: https://newsapi.org/register (free)
- Fallback if key missing: Use RSS feeds via `feedparser`

**RSS Feeds (FALLBACK FOR NEWS — NO KEY NEEDED)**
- BBC News RSS: `http://feeds.bbci.co.uk/news/technology/rss.xml`
- TechCrunch RSS: `https://techcrunch.com/feed/`
- ArXiv CS RSS: `https://rss.arxiv.org/rss/cs`
- Hacker News RSS: `https://news.ycombinator.com/rss`
- Library: `feedparser` (pip install feedparser)

**Open Library API (FOR BOOK/CITATION METADATA — NO KEY)**
- Endpoint: `https://openlibrary.org/api/books?bibkeys=ISBN:xxx&format=json`
- No authentication required
- Use for: Generating book citations from ISBN

**CrossRef API (FOR DOI CITATION LOOKUP — NO KEY)**
- Endpoint: `https://api.crossref.org/works/{DOI}`
- No authentication required (polite pool: add email to User-Agent)
- Use for: Auto-generating citations from DOI
- User-Agent: `ExamHelp/5.0 (mailto:examhelp@example.com)`

**Wikipedia API (FOR RESEARCH/CONTEXT — NO KEY)**
- Endpoint: `https://en.wikipedia.org/api/rest_v1/page/summary/{title}`
- No auth required
- Use for: Quick topic summaries in research mode

**DictionaryAPI.dev (FOR DICTIONARY — NO KEY)**
- Endpoint: `https://api.dictionaryapi.dev/api/v2/entries/en/{word}`
- Completely free, no auth
- Returns: phonetics, meanings, synonyms, antonyms, examples

**Open Exchange Rates — Frankfurter.app (FREE CURRENCY — NO KEY)**
- Endpoint: `https://api.frankfurter.app/latest?from=USD&to=INR,EUR,GBP`
- No auth required
- Use for: Currency context in finance features

**RestCountries API (GEOGRAPHY DATA — NO KEY)**
- Endpoint: `https://restcountries.com/v3.1/name/{country}`
- No auth, completely free

#### B.3 — Media & Content APIs (Free)

**YouTube Transcript API (ALREADY INTEGRATED)**
- Library: `youtube-transcript-api` (pip install youtube-transcript-api)
- No API key needed — scrapes YouTube's public subtitle system
- Fallback language chain: en → en-US → en-GB → a.en → first available

**Unsplash Source (FREE IMAGES — NO KEY FOR DIRECT LINKS)**
- URL pattern: `https://source.unsplash.com/800x400/?{query}`
- No API key for basic image embeds
- Use for: Slide deck visual suggestions

**Pexels API (FREE STOCK PHOTOS)**
- Endpoint: `https://api.pexels.com/v1/search?query={q}&per_page=3`
- Auth: `Authorization: YOUR_KEY` header
- Free tier: 200 requests/hour
- Key: `st.secrets.get("PEXELS_API_KEY", "")` — graceful skip if missing
- Get key: https://www.pexels.com/api/ (free)

#### B.4 — Utility APIs (Free)

**ipinfo.io (IP GEOLOCATION FOR LOCALIZATION — FREE TIER)**
- Endpoint: `https://ipinfo.io/json`
- Free: 50,000 requests/month
- No key needed for basic tier
- Use for: Auto-detecting user region for legal jurisdiction default

**QR Code API (FREE QR GENERATION — NO KEY)**
- Endpoint: `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={text}`
- Returns PNG image directly
- No auth required

#### B.5 — Libraries (All pip install, all free)

```
# Core
streamlit>=1.35.0
requests>=2.31.0
beautifulsoup4>=4.12.0
feedparser>=6.0.11

# AI/ML
google-generativeai>=0.5.0    # Optional Gemini SDK (engine uses REST directly)
groq>=0.9.0

# Document handling
PyMuPDF>=1.24.0               # fitz — PDF extraction
pypdf>=4.0.0                  # PDF fallback
python-docx>=1.1.0
openpyxl>=3.1.0
python-pptx>=0.6.23

# Data
pandas>=2.2.0
numpy>=1.26.0
plotly>=5.20.0

# Text processing
youtube-transcript-api>=0.6.2
newspaper3k>=0.2.8            # Article extraction
lxml>=5.2.0
html5lib>=1.1

# Flashcard export
genanki>=0.13.0               # Anki deck export (optional, graceful skip)

# Math (lazy loaded)
sympy>=1.12

# Code analysis (lazy loaded)
radon>=6.0.1                  # Cyclomatic complexity

# Misc
Pillow>=10.3.0
qrcode>=7.4.2
pyperclip                     # graceful skip if unavailable
python-dotenv>=1.0.0
certifi>=2024.2.2
```

---

## SECTION C — GLOBAL CODING RULES
### (Apply to every single function in every single file)

**RULE-C1 — Error Handling Pattern (Mandatory for every AI call):**
```python
try:
    with st.spinner("🔍 Analyzing…"):
        result = generate(prompt=..., system=..., engine="engine_name")
    if not result or not result.strip():
        st.warning("⚠️ The AI returned an empty response. Please try again.")
        return
    # process result
except Exception as e:
    st.error(f"❌ Something went wrong: {str(e)[:200]}. Please try again in a moment.")
    return
```

**RULE-C2 — Session State Initialization (All keys in init_state()):**
```python
# In app.py::init_state() — add EVERY new key here
DEFAULTS = {
    "messages": [],
    "quiz_data": [],
    "quiz_current": 0,
    "quiz_feedback": None,
    "quiz_score": {"correct": 0, "total": 0},
    "quiz_v2_adaptive_scores": {},
    "flashcard_deck": [],
    "flashcard_index": 0,
    "battle_lifetime_points": 0,
    "tutor_messages": [],
    "pdf_chunks": [],
    "pdf_metadata": {},
    "pomodoro_log": [],
    "note_tags": {},
    "error_log": [],
    "feedback_log": [],
    "session_dates": [],
    "news_cache": {},
    "news_cache_time": 0,
    "research_cache": {},
    "result_cache": {},
    "battle_session": {},
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v
```

**RULE-C3 — Result Caching Pattern (Mandatory for all AI calls):**
```python
import hashlib

def _cache_key(feature: str, text: str) -> str:
    return f"rc_{feature}_{hashlib.md5(text.encode()).hexdigest()[:8]}"

# Before generating:
ck = _cache_key("flashcard", topic_text)
if ck in st.session_state.get("result_cache", {}):
    result = st.session_state["result_cache"][ck]
else:
    result = generate(...)
    st.session_state.setdefault("result_cache", {})[ck] = result
```

**RULE-C4 — Feedback Row (Below every AI output):**
```python
def render_feedback_row(feature: str, result_id: str):
    col1, col2, col3 = st.columns([1, 1, 8])
    with col1:
        if st.button("👍", key=f"up_{feature}_{result_id}"):
            st.session_state["feedback_log"].append({
                "feature": feature, "id": result_id, "vote": "up",
                "timestamp": time.time()
            })
            st.toast("Thanks for your feedback! 🙏")
    with col2:
        if st.button("👎", key=f"dn_{feature}_{result_id}"):
            st.session_state["feedback_log"].append({
                "feature": feature, "id": result_id, "vote": "down",
                "timestamp": time.time()
            })
            st.toast("Got it — we'll improve this! 🔧")
```

**RULE-C5 — Download Button (Below every AI text output):**
```python
st.download_button(
    label="⬇️ Download Result",
    data=result_text,
    file_name=f"{feature_name}_{int(time.time())}.txt",
    mime="text/plain",
    key=f"dl_{feature_name}_{unique_id}",
)
```

**RULE-C6 — Mobile-Safe Columns:**
- Never use `st.columns(3)` or more for primary content
- Use `st.columns([1, 1])` for 2-column layouts
- All CSS widths must be percentage-based, never fixed px

**RULE-C7 — Spinner Messages (Descriptive verbs, never "Loading…"):**
Use: "Generating flashcards…", "Analyzing your code…", "Synthesizing research…",
"Building your quiz…", "Crafting your essay…", "Coaching your interview…"

**RULE-C8 — Input Sanitization (All text inputs):**
```python
from utils.security_utils import sanitize_input
user_text = sanitize_input(st.text_area("Your text", max_chars=10000))
```

**RULE-C9 — Lazy Imports (Heavy libraries):**
```python
# BAD — at module level:
import sympy as sp

# GOOD — inside the function:
def render_math_solver():
    import importlib
    sp = importlib.import_module("sympy")
    # ... use sp
```

**RULE-C10 — No time.sleep() > 0.1s in Streamlit thread:**
Timers, countdowns, and delays MUST use `st.components.v1.html()` with JavaScript
`setInterval()`. Never block the Streamlit render thread.

---

## SECTION D — FILE-BY-FILE IMPLEMENTATION SPECIFICATION

---

### D.1 — `utils/omnikey_engine.py` (CRITICAL FIXES)

Write the COMPLETE file with these exact fixes implemented:

#### FIX-OMK-1: Reset `tried_this_round` After Full Sweep
In `OmniKeyEngine._select_key()`, after completing a full sweep with no available
key, add this logic:
```python
# After full sweep finds no available key:
if len(tried_this_round) >= len(self._slots):
    tried_this_round = set()           # ← RESET so we sweep again
    time.sleep(3.0)                    # ← Wait 3s before next sweep
    if time.monotonic() - wait_start >= MAX_WAIT_FOR_KEY:
        raise RuntimeError(
            f"All {len(self._slots)} Gemini keys are rate-limited. "
            f"Please wait ~{MAX_WAIT_FOR_KEY}s and try again."
        )
    continue                           # ← Continue the while loop
```

#### FIX-OMK-2: Release Global Lock Before HTTP Request
The global `_select_lock` should only protect key slot selection, not the HTTP call:
```python
def execute(self, prompt: str, ...) -> str:
    with self._select_lock:
        slot = self._select_key()      # ← Lock held only here
        slot.mark_in_use()
    # ← Lock released before HTTP
    try:
        response = self._call_api(slot.key, prompt, ...)
        tokens_in, tokens_out = self._parse_token_usage(response)
        slot.mark_success(tokens_in=tokens_in, tokens_out=tokens_out)
        return self._extract_text(response)
    except Exception as e:
        slot.mark_error(e)
        raise
```

#### FIX-OMK-3: Parse Real Token Usage
```python
def _parse_token_usage(self, response_json: dict) -> tuple[int, int]:
    meta = response_json.get("usageMetadata", {})
    tokens_in  = meta.get("promptTokenCount", 0)
    tokens_out = meta.get("candidatesTokenCount", 0)
    return tokens_in, tokens_out
```

#### FIX-OMK-4: Fix Streaming Fallback
When Gemini returns the full response in one block instead of streaming:
```python
def execute_stream(self, prompt: str, ...) -> Iterator[str]:
    # ... make request ...
    text = self._extract_text(response_json)
    if text:
        # Word-tokenize and yield chunks with delay
        words = text.split()
        chunk_size = 4  # yield 4 words at a time
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            yield chunk + " "
            time.sleep(0.03)
    return
```

#### FIX-OMK-5: Proper SSL with Certifi
```python
import certifi
import ssl

def _make_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context(cafile=certifi.where())
    return ctx

# Use this context in all urllib.request calls:
opener = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=_make_ssl_context())
)
```

**ADD: `get_status_report()` method on OmniKeyEngine:**
```python
def get_status_report(self) -> dict:
    now = time.monotonic()
    ready = sum(1 for s in self._slots if s.status == KeyStatus.READY and now >= s.cooldown_until)
    total_in  = sum(s.total_tokens_in  for s in self._slots)
    total_out = sum(s.total_tokens_out for s in self._slots)
    next_ready_in = min(
        (max(0, s.cooldown_until - now) for s in self._slots if s.status != KeyStatus.READY),
        default=0,
    )
    return {
        "total_keys":    len(self._slots),
        "ready_keys":    ready,
        "total_tokens_in":  total_in,
        "total_tokens_out": total_out,
        "next_key_ready_in": round(next_ready_in, 1),
        "health": "good" if ready >= 3 else "degraded" if ready >= 1 else "critical",
    }
```

---

### D.2 — `utils/ai_engine.py` (ENHANCEMENTS)

Write the COMPLETE file. Keep all existing function signatures. Add:

#### ADD-AI-1: `generate_with_retry()`
```python
def generate_with_retry(
    prompt: str,
    max_retries: int = 3,
    **kwargs
) -> str:
    """
    Wrapper around generate() with exponential backoff retry on transient errors.
    Does NOT retry on rate-limit errors (RuntimeError with 'rate' in message).
    """
    import logging
    logger = logging.getLogger("examhelp.ai")
    last_error = None
    for attempt in range(max_retries):
        try:
            return generate(prompt=prompt, **kwargs)
        except RuntimeError as e:
            if "rate" in str(e).lower() or "all" in str(e).lower():
                raise  # Don't retry rate-limit errors
            last_error = e
            wait = 2 ** attempt
            logger.warning(f"generate() attempt {attempt+1} failed: {e}. Retrying in {wait}s…")
            time.sleep(wait)
        except Exception as e:
            last_error = e
            wait = 2 ** attempt
            logger.warning(f"generate() attempt {attempt+1} failed: {e}. Retrying in {wait}s…")
            time.sleep(wait)
    raise RuntimeError(f"generate_with_retry failed after {max_retries} attempts: {last_error}")
```

#### ADD-AI-2: `batch_generate()`
```python
def batch_generate(prompts: list[str], **kwargs) -> list[str]:
    """
    Send multiple prompts concurrently. Returns results in input order.
    Uses max_workers=3 to avoid overwhelming the key pool.
    """
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(generate, prompt=p, **kwargs) for p in prompts]
        return [f.result() for f in futures]
```

#### ADD-AI-3: Fix `json_generate()` with Retry
```python
def json_generate(prompt: str, system: str = "", **kwargs) -> dict | list:
    """
    Generate JSON output from Gemini, with validation and strict-mode retry.
    Returns parsed dict or list. Raises ValueError if JSON cannot be parsed.
    """
    def _try_parse(text: str):
        text = text.strip()
        # Strip markdown fences
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
        text = text.strip()
        return json.loads(text)

    # First attempt
    try:
        raw = generate(prompt=prompt, system=system, **kwargs)
        return _try_parse(raw)
    except (json.JSONDecodeError, ValueError):
        pass

    # Strict retry
    strict_system = (
        (system + "\n\n" if system else "") +
        "CRITICAL: Return ONLY a raw JSON object or array. "
        "No text before or after it. No markdown. No code fences. "
        "Start your response with { or [ and end with } or ]."
    )
    try:
        raw = generate(prompt=prompt, system=strict_system, **kwargs)
        return _try_parse(raw)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"json_generate: Could not parse JSON after retry. Error: {e}. Raw: {raw[:200]}")
```

#### ADD-AI-4: `get_token_usage_summary()`
```python
def get_token_usage_summary() -> dict:
    """
    Returns aggregate token usage across all keys + estimated cost.
    Gemini 2.5 Flash pricing: $0.075/1M input tokens, $0.30/1M output tokens.
    """
    report = OMNI_ENGINE.get_status_report()
    total_in  = report.get("total_tokens_in", 0)
    total_out = report.get("total_tokens_out", 0)
    cost = (total_in / 1_000_000 * 0.075) + (total_out / 1_000_000 * 0.30)
    return {
        "total_in":           total_in,
        "total_out":          total_out,
        "estimated_cost_usd": round(cost, 6),
    }
```

---

### D.3 — `utils/prompts.py` (COMPLETE REGISTRY)

Write the COMPLETE file. Keep all EXISTING ENGINE_PROMPTS entries unchanged.
ADD the following missing entries (every single one, no exceptions):

```python
ENGINE_PROMPTS["flashcard_generate"] = {
    "system": (
        "You are a master flashcard creator for exam preparation. "
        "Given a topic or text, create high-quality question-answer pairs. "
        "Rules:\n"
        "1. Questions must test understanding, NOT just memorization.\n"
        "2. Include 'why' and 'how' questions alongside factual ones.\n"
        "3. Each card must have: q (question), a (answer), topic (string), "
        "   hint (one-word clue), difficulty (Easy/Medium/Hard).\n"
        "4. Answers must be complete but concise (1-3 sentences max).\n"
        "5. Output ONLY a valid JSON array of card objects. No preamble."
    ),
    "temperature": 0.4,
    "max_tokens": 4096,
}

ENGINE_PROMPTS["quiz_generate"] = {
    "system": (
        "You are an expert exam question setter. Generate multiple-choice "
        "questions (MCQs) with exactly 4 options each. "
        "Rules:\n"
        "1. Each question must have: q, options (list of 4), correct (0-indexed int), "
        "   explanation (why the answer is correct), topic, difficulty.\n"
        "2. Wrong options must be plausible — not obviously incorrect.\n"
        "3. Explanation must reference the topic clearly.\n"
        "4. Output ONLY a valid JSON array. No text before or after."
    ),
    "temperature": 0.3,
    "max_tokens": 4096,
}

ENGINE_PROMPTS["essay_writer"] = {
    "system": (
        "You are a Senior Academic Writer with expertise across all disciplines. "
        "Write polished, argument-driven essays. Structure:\n"
        "Introduction (hook + context + thesis)\n"
        "Body Paragraphs (topic sentence + evidence + analysis + transition)\n"
        "Counterargument + Refutation (for argumentative essays)\n"
        "Conclusion (restate thesis + synthesis + call to action or insight).\n"
        "Style: Formal, precise, varied sentence structure. No clichés. "
        "Output ONLY the essay. No preamble."
    ),
    "temperature": 0.65,
    "max_tokens": 12288,
}

ENGINE_PROMPTS["debugger"] = {
    "system": (
        "You are a Senior Software Engineer and Security Auditor. "
        "Analyze code for: bugs (logic errors, off-by-one, null refs), "
        "security vulnerabilities (injection, unsafe eval, hardcoded secrets), "
        "performance issues (O(n²) loops, memory leaks, redundant I/O), "
        "and code quality (naming, DRY, SOLID principles). "
        "Output Format (use exactly these headers):\n"
        "### Bug Report\n"
        "### Security Audit\n"
        "### Performance Analysis\n"
        "### Corrected Code (complete, runnable)\n"
        "### Unit Tests (pytest format, minimum 3 test cases)"
    ),
    "temperature": 0.1,
    "max_tokens": 8192,
}

ENGINE_PROMPTS["interview_coach"] = {
    "system": (
        "You are a Senior Technical and HR Interview Coach at a Fortune 500 company. "
        "Generate role-specific interview questions with model answers. "
        "For behavioural questions: use STAR format (Situation, Task, Action, Result). "
        "For technical questions: include code where applicable. "
        "For system design: include diagrams as ASCII art. "
        "Always include a 'Pitfalls' section (what bad answers look like)."
    ),
    "temperature": 0.4,
    "max_tokens": 6144,
}

ENGINE_PROMPTS["research_synthesis"] = {
    "system": (
        "You are a Research Scholar with a PhD-level understanding of academic methodology. "
        "Synthesize information with academic rigour. "
        "Structure output as:\n"
        "1. Executive Summary\n"
        "2. Key Findings (with source attribution where possible)\n"
        "3. Methodology Critique\n"
        "4. Research Gaps Identified\n"
        "5. Future Research Directions\n"
        "6. Conclusion\n"
        "Maintain objectivity. Note conflicting evidence explicitly."
    ),
    "temperature": 0.3,
    "max_tokens": 8192,
}

ENGINE_PROMPTS["presentation_builder"] = {
    "system": (
        "You are an Elite Presentation Designer and Corporate Storyteller. "
        "Create structured slide decks with a clear narrative arc. "
        "Each slide object must have: title (str), bullets (list of str, max 5), "
        "speaker_notes (str, 2-4 sentences), visual_suggestion (str, describes image), "
        "slide_type (one of: Title|Agenda|Data|Quote|Team|Timeline|ThankYou|Content), "
        "highlight_bullet (int index of most important bullet, 0-indexed). "
        "Output as JSON array of slide objects ONLY. No text before or after. "
        "Follow McKinsey pyramid principle: conclusion first, then supporting evidence."
    ),
    "temperature": 0.5,
    "max_tokens": 8192,
}

ENGINE_PROMPTS["shopping_analyst"] = {
    "system": (
        "You are a Consumer Research Analyst and Deal Expert. "
        "Analyze products with rigorous comparison: "
        "price-to-value ratio, reliability, user sentiment, hidden costs, and alternatives. "
        "Always warn about dark patterns, misleading specs, or inflated original prices. "
        "Structure: Summary Table → Detailed Analysis → Red Flags → Recommendation. "
        "Never recommend a specific retailer. Be vendor-neutral."
    ),
    "temperature": 0.4,
    "max_tokens": 4096,
}

ENGINE_PROMPTS["language_tools"] = {
    "system": (
        "You are a Computational Linguist and Language Learning Expert. "
        "Provide deep linguistic analysis: morphology, syntax, pragmatics, "
        "cultural connotations, and register variations. "
        "For translation: provide 3 variants (literal, natural, formal). "
        "For grammar correction: explain WHY each change was made. "
        "For pronunciation: provide IPA notation + simple phonetic guide. "
        "Always give real usage examples from authentic contexts."
    ),
    "temperature": 0.3,
    "max_tokens": 3072,
}

ENGINE_PROMPTS["study_planner"] = {
    "system": (
        "You are an Academic Success Coach and Cognitive Scientist. "
        "Create scientifically-grounded study plans based on spaced repetition, "
        "interleaving, and retrieval practice principles. "
        "Output a day-by-day schedule with for each day: date, topics (list), "
        "technique (one of: Active Recall|Spaced Repetition|Interleaving|Elaboration|Feynman), "
        "duration_hours (float), confidence_checkpoint (question to self-test readiness). "
        "Output as JSON array of day objects. Heavy review early, light review before exam."
    ),
    "temperature": 0.4,
    "max_tokens": 4096,
}

ENGINE_PROMPTS["citation_generator"] = {
    "system": (
        "You are a specialist academic librarian with expertise in citation formatting. "
        "Format citations with 100% accuracy per the requested style guide. "
        "If source info is incomplete, state which fields are missing. "
        "Output ONLY the formatted citation string — no preamble, no explanation."
    ),
    "temperature": 0.1,
    "max_tokens": 512,
}

ENGINE_PROMPTS["regex_explainer"] = {
    "system": (
        "You are a master of regular expressions with 20 years of experience. "
        "Explain regex patterns in plain English, token by token. "
        "For each token: what it matches, why it's used, common pitfalls. "
        "Then give 3 example strings that match and 3 that don't."
    ),
    "temperature": 0.2,
    "max_tokens": 1024,
}

ENGINE_PROMPTS["code_complexity"] = {
    "system": (
        "You are a Senior Software Architect specializing in code quality. "
        "Analyze code complexity, maintainability, and technical debt. "
        "Use standard metrics: Cyclomatic Complexity (McCabe), Cognitive Complexity, "
        "Halstead metrics. Flag: god functions (>50 lines), deep nesting (>4 levels), "
        "duplicate logic, and violation of Single Responsibility Principle."
    ),
    "temperature": 0.1,
    "max_tokens": 4096,
}

ENGINE_PROMPTS["salary_negotiation"] = {
    "system": (
        "You are a compensation expert and negotiation strategist. "
        "Provide precise, tactical, data-informed salary advice. "
        "Structure: Market range (low/median/high) → Negotiation script → "
        "Counter-offer template → Red lines (what not to accept) → "
        "Timing strategy (when to negotiate, when to wait). "
        "Be direct and specific. No generic platitudes."
    ),
    "temperature": 0.3,
    "max_tokens": 3072,
}

ENGINE_PROMPTS["legal_analyser"] = {
    "system": (
        "You are a Senior Legal Counsel with expertise across multiple jurisdictions. "
        "Analyze legal scenarios with academic rigour. Always: "
        "1. Identify the jurisdiction and applicable legal framework. "
        "2. State the relevant statutes and case precedents. "
        "3. Apply the IRAC method (Issue, Rule, Application, Conclusion). "
        "4. Note dissenting views or legal ambiguities. "
        "DISCLAIMER REQUIRED: End every response with: "
        "'⚖️ This analysis is for educational purposes only. "
        "Consult a qualified legal professional for actual legal advice.'"
    ),
    "temperature": 0.15,
    "max_tokens": 6144,
}

ENGINE_PROMPTS["medical_research"] = {
    "system": (
        "You are a Medical Research Educator with clinical and academic expertise. "
        "Explain medical concepts, pathophysiology, and pharmacology with precision. "
        "Use: ICD codes where relevant, drug generic names, evidence grades (Level I-IV). "
        "Structure complex topics: Epidemiology → Pathophysiology → Clinical Features → "
        "Investigations → Management → Complications → Prognosis. "
        "MANDATORY DISCLAIMER: End EVERY response with: "
        "'⚠️ FOR EDUCATIONAL AND RESEARCH USE ONLY. NOT MEDICAL ADVICE. "
        "Always consult a qualified healthcare professional for clinical decisions.'"
    ),
    "temperature": 0.2,
    "max_tokens": 6144,
}

ENGINE_PROMPTS["drug_interaction"] = {
    "system": (
        "You are a Clinical Pharmacologist. Analyze drug interactions with: "
        "1. Mechanism (pharmacokinetic/pharmacodynamic) "
        "2. Severity (Contraindicated/Major/Moderate/Minor) "
        "3. Clinical significance and onset "
        "4. Management recommendation "
        "5. Alternative drugs to consider "
        "Output as structured markdown. Always include the disclaimer: "
        "'⚠️ NOT FOR CLINICAL DECISION-MAKING. Verify with pharmacist or prescriber.'"
    ),
    "temperature": 0.1,
    "max_tokens": 3072,
}

ENGINE_PROMPTS["note_enhancer"] = {
    "system": (
        "You are a Study Coach and Academic Writing Specialist. "
        "Enhance bullet-point notes into comprehensive, exam-ready study material. "
        "For each bullet: expand to 2-3 sentences, add a definition for technical terms "
        "in parentheses, and end with one insight or connection to other concepts. "
        "Return the enhanced notes in the same structure. Output only the enhanced notes."
    ),
    "temperature": 0.5,
    "max_tokens": 4096,
}

ENGINE_PROMPTS["plagiarism_check"] = {
    "system": (
        "You are an AI writing detection specialist and academic integrity expert. "
        "Analyze text for signs of AI-generated or unoriginal content. "
        "Rate each dimension 1-10 (10 = most human/original):\n"
        "- Voice Authenticity (personal, unique perspective)\n"
        "- Structural Variety (sentence rhythm, paragraph length variety)\n"
        "- Specificity of Examples (concrete vs. generic examples)\n"
        "- Transition Naturalness (varied vs. formulaic transitions)\n"
        "- Overall Originality Score (weighted average)\n"
        "Then provide exactly 3 specific rewrite suggestions with before/after examples. "
        "Be constructive and precise."
    ),
    "temperature": 0.3,
    "max_tokens": 2048,
}

ENGINE_PROMPTS["research_gap"] = {
    "system": (
        "You are a Research Director with experience across STEM and humanities. "
        "Identify research gaps with scholarly depth. "
        "For each gap: why it matters, suggested methodology, feasibility rating (1-5), "
        "potential funding sources (NSF, NIH, Wellcome Trust, etc.), "
        "and a draft research question in PICO format where applicable. "
        "Output as a structured markdown report with a summary table."
    ),
    "temperature": 0.4,
    "max_tokens": 6144,
}

ENGINE_PROMPTS["company_research"] = {
    "system": (
        "You are a Strategic Intelligence Analyst specializing in corporate research. "
        "Generate a concise but comprehensive company intelligence brief covering: "
        "Business model & revenue streams, culture & values (Glassdoor themes), "
        "recent strategic moves & news angles, likely organizational pain points, "
        "interview culture (structured/unstructured, technical depth), "
        "smart questions to ask the interviewer, and red flags to watch for. "
        "Be specific and actionable. Base on verifiable public information."
    ),
    "temperature": 0.4,
    "max_tokens": 4096,
}
```

---

### D.4 — `utils/flashcard_engine.py` (COMPLETE)

Write the full file with these additions/fixes on top of the existing v2.0 code:

#### Must include all of these functions (complete implementations):

**`validate_cards(cards: list) -> list`** — Already exists, verify implementation matches spec

**`_generate_cards_task(context_text, lang, count, easy_pct, medium_pct, hard_pct)`**
The prompt MUST include:
```
"DIFFICULTY DISTRIBUTION (strictly enforce):
- Easy: {easy_n} cards — straightforward, factual, single-step recall
- Medium: {medium_n} cards — application and understanding required
- Hard: {hard_n} cards — analysis, synthesis, multi-step reasoning

Every card MUST have ALL fields: q, a, topic, hint, difficulty
topic field must be derived from the content, never empty.
Output ONLY a valid JSON array. First character must be [. Last character must be ]."
```

**`render_battle_mode(deck: list)`** — Complete battle mode UI:
- JavaScript countdown timer via `st.components.v1.html()` (no `time.sleep()`)
- Three-tier answer scoring: exact match → numerical match → keyword overlap
- Power-up system: 3 correct in a row = +5 bonus points + celebration message
- Mastery heatmap at end: HTML table, 7 difficulty buckets × topics, green/yellow/red cells
- CSV export: Question, Answer, Topic, Difficulty, Hint columns

**`render_ai_tutor(deck: list)`** — Complete AI tutor UI:
- Sliding window: always pin first system message, keep last 6 user/assistant turns
- "Explain Like I'm 5" button — reformats last AI response with analogy
- "Generate Practice Problem" button — creates a custom exercise from selected topic

**`export_to_anki(deck: list) -> bytes`** — Export as .apkg (if genanki available) or
as .csv fallback with proper Anki import format.

---

### D.5 — `utils/quiz_engine.py` (COMPLETE)

Write the full file. Must include:

**`generate_quiz_batch(context_text, is_pyq, pyq_text, difficulty, num_q) -> list`**
Prompt must force JSON array output.
Post-process: validate each question has q, options (list of 4), correct (0-3 int), explanation, topic, difficulty.

**`render_quiz_ui(quiz_data: list)`** — Main quiz loop:
- BOUNDS CHECK before every question render:
  ```python
  if st.session_state.quiz_current >= len(st.session_state.quiz_data):
      st.session_state.quiz_current = 0
      st.warning("Quiz reset — question count changed.")
      st.rerun()
  ```
- TWO-PHASE answer pattern (never auto-advance):
  Phase 1: Show feedback ("✅ Correct!" or "❌ Incorrect!") + explanation
  Phase 2: "Next Question →" button increments index and reruns

**`get_next_question_difficulty(scores: dict, topic: str) -> str`** — Already exists

**`render_quiz_analytics(history: list)`**:
- Trend line chart: Plotly line chart, x=attempt number, y=rolling 5-question accuracy
- "Weak Spot Driller" button: generates 5 targeted questions on worst-performing topic
- Report download as formatted .txt file

---

### D.6 — `utils/essay_engine.py` (COMPLETE)

Write the full file. Must include:

**`generate_essay(topic, essay_type, academic_level, word_count, citation_style, extra_instructions) -> str`**:
- For word_count > 1000: set max_tokens=12288
- For word_count > 2000: chunked generation:
  1. Generate outline (section headers + 1-sentence summaries)
  2. Generate each section independently with outline as context
  3. Stitch sections together with coherence pass

**`generate_outline(topic, essay_type, academic_level) -> str`** — Outline generator

**`improve_essay(existing_essay: str) -> str`** — Enhancement pass

**`check_originality(essay_text: str) -> dict`** — AI-powered originality check:
Uses ENGINE_PROMPTS["plagiarism_check"]. Returns dict with scores and suggestions.
Displays as a styled scorecard with 5 color-coded metric bars (red=low, green=high).

**`cowrite_continuation(existing_essay: str, section: str, instruction: str) -> str`**:
- Sends FULL existing essay as context (up to 8000 chars)
- Instruction: "Do NOT rewrite what already exists. ONLY write the new {section}."
- After generation, show diff: left = existing last 500 chars, right = new addition

---

### D.7 — `utils/debugger_engine.py` (COMPLETE)

Write the full file. Must include:

**`sanitize_code_for_prompt(code: str, language: str) -> str`**:
Wrap in XML tags to prevent prompt injection:
```python
return f'<code language="{language}">\n{code}\n</code>'
```

**`quick_syntax_check(code: str, language: str) -> tuple[bool, str]`**:
For Python: use `ast.parse()` to catch syntax errors before API call.
For other languages: skip pre-check, return (True, "").

**`analyze_code(code, language, error_msg, expected_output) -> str`**:
Uses ENGINE_PROMPTS["debugger"]. Sanitizes code with XML tags.
Runs quick_syntax_check first — if syntax error found, display immediately without API call.

**`render_diff_view(original: str, fixed: str)`**:
```python
import difflib
diff = list(difflib.unified_diff(original.splitlines(), fixed.splitlines(), lineterm="", n=3))
```
Render as HTML: deletions = red background `#3d1212`, additions = green `#123d12`.
Use `st.markdown(html_string, unsafe_allow_html=True)`.

**`analyze_complexity(code: str) -> dict`** (lazy import radon):
```python
def analyze_complexity(code: str) -> dict:
    try:
        import radon.complexity as rc
        import radon.metrics as rm
        blocks = rc.cc_visit(code)
        results = []
        for block in blocks:
            results.append({
                "name": block.name,
                "complexity": block.complexity,
                "grade": rc.cc_rank(block.complexity),
                "lineno": block.lineno,
            })
        mi = rm.mi_visit(code, multi=True)
        return {"functions": results, "maintainability_index": round(mi, 1)}
    except ImportError:
        return {"error": "radon not installed. Run: pip install radon"}
    except Exception as e:
        return {"error": str(e)}
```

**`security_audit(code: str, language: str) -> str`**:
Specialized security-focused prompt: OWASP Top 10, injection, hardcoded secrets,
unsafe deserialization, path traversal. Plus regex scan for hardcoded secret patterns:
```python
secret_patterns = [
    r'password\s*=\s*["\'][^"\']+["\']',
    r'api_key\s*=\s*["\'][^"\']+["\']',
    r'secret\s*=\s*["\'][^"\']+["\']',
    r'token\s*=\s*["\'][^"\']+["\']',
]
```

**`generate_tests(code: str, language: str) -> str`**:
Generates pytest tests for every detected function. Covers happy path, edge cases
(None, empty, max int), and expected exception cases.

---

### D.8 — `utils/interview_engine.py` (COMPLETE)

Write the full file. Must include:

**`generate_questions(role, company, interview_type, experience, num_questions) -> str`**:
Inject role-specific depth:
- Technical roles: 40% technical, 30% system design, 30% behavioural
- Non-technical roles: 20% domain knowledge, 80% behavioural
- Include code snippets in expected answers for technical questions

**`run_mock_interview(role, company, messages: list) -> str`**:
Full conversational loop. System prompt includes full message history.
After 5 exchanges: generate detailed evaluation scorecard.
System prompt:
```
You are a tough but fair interviewer at {company} for {role}.
Questions asked so far: {len(messages)//2}.
Rules:
- Ask ONE focused follow-up to the candidate's last answer.
- If vague: probe deeper. If strong: raise the bar.
- After 5+ exchanges: provide a 6-dimension scorecard.
```

**`generate_tell_me_about_yourself(role, company, experience_points: list) -> str`**:
90-second verbal script. Optimized for impact with hook, value proposition, fit signal.

**`generate_salary_strategy(role, location, years_exp) -> str`**:
Uses ENGINE_PROMPTS["salary_negotiation"]. Returns: market range, negotiation script,
counter-offer template, red lines.

**`generate_company_brief(company: str) -> str`**:
Uses ENGINE_PROMPTS["company_research"]. Returns structured 1-page intelligence brief.

**`generate_case_timeline(legal_scenario: str, jurisdiction: str) -> str`**:
For legal interview type: chronological proceedings timeline with estimated durations.

---

### D.9 — `utils/pdf_handler.py` (COMPLETE)

Write the full file with all existing functions. Must include:

**`chunk_pdf_text(text: str) -> list[str]`** — Already exists, verify:
CHUNK_SIZE_CHARS = 8000, CHUNK_OVERLAP_CHARS = 800. Returns list of overlapping chunks.

**`find_relevant_chunks(query: str, chunks: list[str], top_k: int = 3) -> list[str]`**:
TF-IDF style relevance scoring:
```python
def find_relevant_chunks(query: str, chunks: list[str], top_k: int = 3) -> list[str]:
    query_words = set(query.lower().split())
    def score_chunk(chunk: str) -> float:
        chunk_words = chunk.lower().split()
        if not chunk_words:
            return 0.0
        matches = sum(1 for w in chunk_words if w in query_words)
        return matches / len(chunk_words)
    scored = sorted(enumerate(chunks), key=lambda x: score_chunk(x[1]), reverse=True)
    return [chunks[i] for i, _ in scored[:top_k]]
```

**`get_pdf_metadata(file_bytes: bytes) -> dict`**:
Returns: page_count, file_size_kb, estimated_reading_time_min,
detected_language (from first page text), has_toc (bool).

**`extract_chapters(text: str) -> list[dict]`**:
Detect headings via uppercase lines, numbered headings, or lines ending with colon.
Return list of {title, content} dicts. If fewer than 2 chapters detected, return empty list.

**`summarize_by_chapter(file_bytes: bytes) -> list[dict]`**:
Calls extract_chapters() then generates a separate AI summary for each chapter.

---

### D.10 — `utils/youtube_handler.py` (COMPLETE)

Write the full file. Must include:

**`get_transcript(url: str) -> tuple[str, str, str]`**:
Returns (transcript_text, language_used, error_message).
Language fallback chain: en → en-US → en-GB → a.en → first available.
On TranscriptsDisabled: return ("", "", helpful guidance message — don't crash).

**`format_with_timestamps(transcript_entries: list, interval: int = 60) -> str`**:
Inserts `[MM:SS]` markers every `interval` seconds.

**`answer_with_timestamp(transcript_entries: list, question: str, video_id: str) -> str`**:
Sends transcript + question to AI. AI should identify the most relevant timestamp.
Parse timestamp from response. Return answer + YouTube URL with `?t={seconds}` param:
```python
yt_url = f"https://youtu.be/{video_id}?t={timestamp_seconds}"
```

**`get_video_id(url: str) -> str`** — Already exists, verify handles Shorts and Live URLs.

---

### D.11 — `utils/web_handler.py` (COMPLETE)

Write the full file. Must include:

**`scrape_url(url: str, check_robots: bool = True) -> tuple[str, str]`**:
Returns (cleaned_content, error_message).
Content extraction heuristics:
1. Remove: nav, footer, header, aside, script, style, form, button, iframe, noscript
2. Try selectors in order: article, [role=main], main, .post-content, .article-content, .entry-content, #content, #main-content
3. Take the longest matching block
4. Clean with `_clean_text()`

**`check_robots_txt(url: str) -> tuple[bool, str]`**:
Fetch `{scheme}://{netloc}/robots.txt`.
Check if the URL path is disallowed for user-agent `*`.
Return (is_allowed, reason_string).
On any exception (robots.txt missing): return (True, "No robots.txt found — proceeding").

**`_clean_text(text: str) -> str`** — Already exists, verify implementation.

---

### D.12 — `utils/citation_engine.py` (COMPLETE)

Write the full file. Must include:

**`generate_citation(source: str, style: str) -> str`** — Already exists.

**`bulk_generate_citations(sources: list[str], style: str) -> list[str]`**:
Uses `batch_generate()` from ai_engine for parallel processing.
Returns citations in same order as input.

**`lookup_doi_metadata(doi: str) -> dict`**:
Query CrossRef API: `https://api.crossref.org/works/{doi}`
Parse: title, authors, publisher, year, journal, volume, issue, pages.
Return dict. On error: return {"error": "DOI not found"}.
User-Agent: `ExamHelp/5.0 (mailto:examhelp@example.com)`

**`format_as_bibtex(citations: list[str], sources: list[str]) -> str`**:
Convert formatted citations to BibTeX format using AI.
Return complete .bib file content as string.

**`format_as_ris(citations: list[str]) -> str`**:
Convert to RIS format (for Zotero/Mendeley).
Return .ris file content as string.

Citation styles to support (7 total):
APA 7th | MLA 9th | Chicago 17th Notes | Chicago 17th Author-Date | IEEE | Harvard | Vancouver

---

### D.13 — `utils/regex_engine.py` (COMPLETE)

Write the full file. Must include:

**`generate_regex(description: str, examples: list) -> dict`** — Already exists.

**`highlight_matches(pattern: str, text: str) -> str`**:
Returns HTML string with matches wrapped in `<mark>` tags.
Invalid regex: return error message in red span.
No matches: return text in muted color span.
Use `html.escape()` on all text BEFORE inserting tags.

**`explain_regex(pattern: str) -> str`**:
Uses ENGINE_PROMPTS["regex_explainer"]. Token-by-token explanation.

**`get_match_details(pattern: str, text: str, flags: str = "") -> dict`**:
Run `re.finditer()`. Return:
```python
{
    "match_count": int,
    "matches": [{"text": str, "start": int, "end": int, "groups": list}],
    "is_valid": bool,
    "error": str,
}
```

**`generate_substitution_preview(pattern: str, replacement: str, text: str) -> str`**:
Apply `re.sub(pattern, replacement, text)`. Return modified text or error string.

---

### D.14 — `utils/security_utils.py` (COMPLETE)

Write the full file. Must include:

**`mask_api_key(key: str) -> str`** — Shows first 4 + last 4, masks middle.

**`sanitize_input(text: str, max_length: int = 10000) -> str`**:
```python
def sanitize_input(text: str, max_length: int = 10_000) -> str:
    if not isinstance(text, str):
        text = str(text)
    text = text.replace('\x00', '')     # Remove null bytes
    text = text.strip()                 # Strip whitespace
    if len(text) > max_length:
        # Warn via session state flag, then truncate
        import streamlit as st
        st.warning(f"⚠️ Input truncated to {max_length:,} characters.")
        text = text[:max_length]
    return text
```

**`validate_gemini_key(key: str) -> bool`**:
```python
def validate_gemini_key(key: str) -> bool:
    return (
        isinstance(key, str) and
        key.startswith("AIza") and
        len(key) == 39
    )
```

**`log_error(feature: str, error: Exception, context: dict = None)`**:
Append to `st.session_state["error_log"]`. Truncate error message to 500 chars.

**`rate_limit_check(key: str, limit_per_minute: int = 10) -> bool`**:
Using session state timestamp tracking. Return True if under limit.

---

### D.15 — `utils/notes_engine.py` (COMPLETE)

Write the full file (or rewrite the existing `notes_engine.py` at root level). Must include:

**`parse_tags(note_text: str) -> list[str]`**:
Extract #hashtags from note text. Return list of lowercase tag strings without #.

**`add_note(text: str, title: str = "") -> dict`**:
Create note dict with: id (uuid4 hex), title, text, tags, created_at, keywords.
keywords = top 10 most frequent non-stopword words.
Store in `st.session_state["notes_list"]`.

**`find_related_notes(note_id: str, notes: list) -> list[dict]`**:
Find notes sharing ≥3 common keywords with the given note.
Return list of related note dicts sorted by keyword overlap count.

**`enhance_note_with_ai(note_text: str) -> str`**:
Uses ENGINE_PROMPTS["note_enhancer"]. Returns enhanced note text.

**`get_notes_by_tag(tag: str, notes: list) -> list[dict]`**:
Filter notes where tag is in their tags list.

**`render_tag_cloud(notes: list)`**:
Count all tags across notes. Render as HTML tag cloud with font-size proportional to frequency.

---

### D.16 — `utils/vit_engine.py` (COMPLETE)

Write the full file. Must include all existing functions plus:

**`calculate_cgpa(courses: list[dict]) -> dict`** — Already exists, verified.

**`cgpa_credit_planner(current_courses, target_cgpa) -> dict`** — Already exists, verified.

**`simulate_grade_improvement(current_courses, target_cgpa) -> list[dict]`**:
Find which courses, if improved to grade S or A, would most efficiently raise CGPA.
Return list sorted by "impact per credit" descending.

**`generate_timetable(slots: list[str], subjects: list[str]) -> dict`**:
VIT slot-based timetable generator.
VIT Theory slots: A1-F2, TH1-TH6.
VIT Lab slots: L1-L60.
Returns a weekly grid dict: {day: {period: subject_or_empty}}.

**`calculate_attendance(present: int, total: int) -> dict`**:
Returns: percentage, is_safe (>=75%), classes_can_miss (to stay at 75%), 
classes_needed_to_recover (if below 75%).

---

### D.17 — `utils/analytics.py` (COMPLETE)

Write the full file. Must include:

**`render_analytics_dashboard()`**:
All Plotly charts. Every chart handles edge cases:
- Radar chart: enforce minimum 3 axes (add "Other" categories with 0 score if needed)
- Bar charts: handle empty data gracefully

**`calculate_streak(session_dates: list[str]) -> int`**:
session_dates is list of ISO date strings. Calculate consecutive-day streak ending today.

**`render_streak_display(streak: int)`**:
Show 🔥 fire emoji counter. Calendar heatmap for last 30 days using Plotly.

**`render_activity_heatmap(session_dates: list[str])`**:
GitHub-contribution-style 30-day grid using Plotly heatmap.

---

### D.18 — `app.py` (ADDITIONS)

Keep all existing structure. Add/fix:

**`init_state()`**: Initialize ALL session state keys listed in RULE-C2. Every key
must have the correct default type. This function runs at the TOP of app.py before any other logic.

**Sidebar API Status (FIX-11.1a)**:
Replace raw technical data with simplified health dashboard:
```python
def render_api_status():
    report = OMNI_ENGINE.get_status_report()
    health = report["health"]
    icon = {"good": "🟢", "degraded": "🟡", "critical": "🔴"}.get(health, "⚪")
    st.sidebar.metric(f"{icon} API Pool", f"{report['ready_keys']}/{report['total_keys']} keys")
    if report["next_key_ready_in"] > 0:
        st.sidebar.caption(f"Next key ready in {report['next_key_ready_in']}s")
    usage = get_token_usage_summary()
    st.sidebar.caption(f"Tokens used: {usage['total_in'] + usage['total_out']:,}")
```

**Sidebar Emergency Reset Button**:
```python
with st.sidebar.expander("⚠️ Advanced"):
    if st.button("🔄 Emergency Reset"):
        if st.session_state.get("_confirm_reset", False):
            keys_to_keep = [k for k in st.session_state if "key" in k.lower()]
            for k in list(st.session_state.keys()):
                if k not in keys_to_keep:
                    del st.session_state[k]
            st.success("Session reset!")
            st.rerun()
        else:
            st.session_state["_confirm_reset"] = True
            st.warning("Click again to confirm reset.")
```

**Remove global SSL override**: Delete or comment out any `ssl._create_unverified_context`
or `ssl._create_default_https_context` assignment from app.py.

---

### D.19 — `advanced_features.py` (KEY FIXES)

Write complete implementations for all render functions that currently have stubs.
Key fixes:

**`render_pomodoro_timer()`** — Replace `time.sleep()` with JS countdown:
```python
def render_pomodoro_timer():
    work_min = st.slider("Work duration (minutes)", 5, 60, 25)
    break_min = st.slider("Break duration (minutes)", 1, 30, 5)
    
    if st.button("▶️ Start Pomodoro"):
        st.session_state["pomodoro_start"] = time.time()
        st.session_state["pomodoro_duration"] = work_min * 60
    
    if st.session_state.get("pomodoro_start"):
        seconds = work_min * 60
        timer_html = f"""
        <div style="text-align:center;padding:20px;">
            <div id="timer" style="font-size:4rem;font-weight:900;color:#a78bfa;
                 font-family:monospace;">{work_min:02d}:00</div>
            <div id="status" style="color:#94a3b8;margin-top:10px;">Focus Mode 🎯</div>
        </div>
        <script>
        (function() {{
            let remaining = {seconds};
            const display = document.getElementById('timer');
            const status = document.getElementById('status');
            const interval = setInterval(() => {{
                remaining--;
                const m = Math.floor(remaining/60).toString().padStart(2,'0');
                const s = (remaining%60).toString().padStart(2,'0');
                display.textContent = m + ':' + s;
                if (remaining <= 0) {{
                    clearInterval(interval);
                    display.textContent = '00:00';
                    status.textContent = '✅ Session complete! Take a break.';
                    display.style.color = '#4ade80';
                    try {{
                        const ctx = new (window.AudioContext||window.webkitAudioContext)();
                        const osc = ctx.createOscillator();
                        osc.connect(ctx.destination);
                        osc.frequency.value = 440;
                        osc.start();
                        setTimeout(() => osc.stop(), 500);
                    }} catch(e) {{}}
                }}
            }}, 1000);
        }})();
        </script>
        """
        st.components.v1.html(timer_html, height=150)
```

**`render_focus_music()`** — Study music options:
```python
STUDY_PLAYLISTS = {
    "🎵 Lo-Fi Hip-Hop": "https://www.youtube.com/watch?v=jfKfPfyJRdk",
    "🎼 Classical (Mozart Effect)": "https://www.youtube.com/watch?v=Fmtsl9H4i3Q",
    "🧠 Binaural Beats 40Hz Gamma": "https://www.youtube.com/watch?v=7W1qEAhwH1E",
    "🟫 Brown Noise": "https://www.youtube.com/watch?v=RqzGzwTY-6w",
}
```
Display as clickable links that open in new tab.

**`render_regex_tester()`** — Live highlighting:
```python
def render_regex_tester():
    from utils.regex_engine import highlight_matches, explain_regex, get_match_details
    pattern = st.text_input("Regex Pattern", placeholder="e.g. ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")
    test_text = st.text_area("Test String", placeholder="Paste text to test against your pattern...")
    flags_input = st.multiselect("Flags", ["Ignore Case", "Multiline", "Dot All"])
    
    if pattern and test_text:
        highlighted_html = highlight_matches(pattern, test_text)
        st.markdown("**Live Matches:**")
        st.markdown(f'<div style="...border...padding...">{highlighted_html}</div>', unsafe_allow_html=True)
        details = get_match_details(pattern, test_text)
        st.metric("Matches Found", details["match_count"])
    
    if pattern and st.button("🔍 Explain This Regex"):
        with st.spinner("Analyzing pattern…"):
            explanation = explain_regex(pattern)
        st.markdown(explanation)
```

**`render_vit_academics()`** — Complete CGPA calculator:
```python
def render_vit_academics():
    from utils.vit_engine import calculate_cgpa, cgpa_credit_planner
    
    st.subheader("📊 VIT CGPA Calculator")
    num_courses = st.number_input("Number of courses", 1, 20, 6)
    courses = []
    for i in range(num_courses):
        c1, c2, c3 = st.columns(3)
        with c1: name = st.text_input(f"Course {i+1}", key=f"cn_{i}")
        with c2: credits = st.number_input("Credits", 1, 5, 3, key=f"cr_{i}")
        with c3: grade = st.selectbox("Grade", ["S","A","B","C","D","E","F"], key=f"gr_{i}")
        if name:
            courses.append({"name": name, "credits": credits, "grade": grade})
    
    if courses and st.button("Calculate CGPA"):
        result = calculate_cgpa(courses)
        col1, col2, col3 = st.columns(3)
        col1.metric("CGPA", result["cgpa"])
        col2.metric("Total Credits", result["total_credits"])
        col3.metric("Classification", result["classification"])
    
    target = st.slider("Target CGPA", 5.0, 10.0, 8.5, 0.1)
    if courses and st.button("Plan for Target"):
        plan = cgpa_credit_planner(courses, target)
        st.info(plan.get("message", f"You need {plan.get('needed_credits', '?')} more credits at S/A grade."))
```

**`render_citation_generator()`** — All 7 styles, bulk mode, export options.

**`render_news_hub()`** — Deduplicated news with article summarizer.

---

### D.20 — `new_features.py` (ELITE EXPERT ENGINES)

Write complete implementations for all 9 elite engines. Key specifications:

**Circuit Solver Pro:**
- Strict upload validation: `if uploaded_file is None: st.info(...); st.stop()`
- Image preprocessing: grayscale conversion, contrast enhancement with PIL
- Manual circuit input mode as text alternative
- LaTeX output toggle using `st.latex()`

**Advanced Math Solver:**
- Lazy import sympy inside function
- Graph plotter: Plotly line chart for single-variable expressions
- Step-by-step LaTeX rendering for each equation step
- "Check My Work" mode: user inputs solution steps, AI verifies each step

**Legal Analyser:**
- Jurisdiction selector: India / USA / UK / EU / International
- Case timeline generator
- IRAC method structure enforced in prompt

**Medical Research Guide:**
- Disclaimer injected into EVERY response via `add_medical_disclaimer()` wrapper
- Drug interaction checker using ENGINE_PROMPTS["drug_interaction"]

**Research Scholar:**
- Citation network via Mermaid.js diagram
- Research gap analysis table with 5+ identified gaps
- Literature review matrix as HTML table (papers × attributes)

**Technical Project Architect:**
- Tech Decision Log table required in every blueprint
- Mermaid.js architecture diagram auto-generated

**Elite Stocks Dashboard:**
- PERMANENT non-dismissible red banner:
  ```python
  st.markdown("""
  <div style="background:#7f1d1d;border:2px solid #ef4444;border-radius:8px;
              padding:16px;margin-bottom:20px;position:sticky;top:0;z-index:999;">
  🚨 <strong>IMPORTANT DISCLAIMER:</strong> ALL stock data and analysis shown here are 
  AI-GENERATED ESTIMATES for EDUCATIONAL PURPOSES ONLY. This is NOT real financial data. 
  Do NOT make investment decisions based on this tool. For real data, use NSE/BSE official 
  websites or consult a SEBI-registered financial advisor.
  </div>
  """, unsafe_allow_html=True)
  ```
- No specific price targets. No Buy/Sell recommendations. Qualitative analysis only.

**AI Dictionary & Lexicon:**
- IPA + phonetic pronunciation guide (from DictionaryAPI.dev)
- Word family tree as Mermaid mindmap
- Word frequency meter across registers (Academic/Journalism/Conversation)
- Fetch from `https://api.dictionaryapi.dev/api/v2/entries/en/{word}` first (free, no key)
- Fall back to AI generation if API fails

**Professional HTML Page Builder:**
- System prompt constraint: "ONLY standard Tailwind utility classes via CDN. NO arbitrary values like w-[342px]."
- Post-generation regex scan: detect `\[[\d.]+[a-z]*\]` patterns → warn user with yellow callout
- Netlify Drop instructions: "Download this file and drag to netlify.com/drop for instant free hosting"
- Show live preview in `st.components.v1.html()` iframe

---

## SECTION E — INTEGRATION MAP
### (Where Each Free API Gets Used — Complete Reference)

| Feature | API/Library | Key Required | Endpoint/Usage |
|---------|------------|--------------|----------------|
| All AI features | Gemini 2.5 Flash | YES (GEMINI_API_KEY_1-9 via st.secrets) | REST via omnikey_engine.py |
| Voice transcription | Groq Whisper | YES (GROQ_API_KEY via st.secrets) | https://api.groq.com/openai/v1/audio/transcriptions |
| Voice fallback | Gemini Audio | Uses main pool | Gemini generateContent with audio part |
| News Hub | NewsAPI.org | YES (NEWS_API_KEY via st.secrets) | https://newsapi.org/v2/everything |
| News fallback | feedparser RSS | NO | Multiple RSS feeds |
| YouTube Q&A | youtube-transcript-api | NO | Python library, no key |
| Web scraping | requests + BS4 | NO | Direct HTTP GET |
| DOI lookup | CrossRef API | NO | https://api.crossref.org/works/{doi} |
| ISBN lookup | Open Library | NO | https://openlibrary.org/api/books |
| Dictionary (word lookup) | DictionaryAPI.dev | NO | https://api.dictionaryapi.dev/api/v2/entries/en/{word} |
| Images for slides | Unsplash Source | NO | https://source.unsplash.com/800x400/?{query} |
| PDF extraction | PyMuPDF (fitz) | NO | pip install PyMuPDF |
| Code complexity | radon | NO | pip install radon (lazy import) |
| Math solving | sympy | NO | pip install sympy (lazy import) |
| Anki export | genanki | NO | pip install genanki (optional, graceful skip) |
| QR codes | api.qrserver.com | NO | https://api.qrserver.com/v1/create-qr-code/ |
| Article extraction | newspaper3k | NO | pip install newspaper3k (lazy import) |

---

## SECTION F — TESTING REQUIREMENTS

Add to `tests/test_v5_suite.py`:

### F.1 — Unit Tests (All must pass with no network calls):

```python
# test validate_cards
def test_validate_cards_missing_fields():
    from utils.flashcard_engine import validate_cards
    bad = [{"q": "Q1"}]  # missing a, topic, hint, difficulty
    assert validate_cards(bad) == []

def test_validate_cards_normalizes_difficulty():
    from utils.flashcard_engine import validate_cards
    card = {"q": "Q", "a": "A", "topic": "T", "hint": "H", "difficulty": "medium"}
    result = validate_cards([card])
    assert result[0]["difficulty"] == "Medium"

# test calculate_cgpa
def test_calculate_cgpa_all_s():
    from utils.vit_engine import calculate_cgpa
    courses = [{"name": "Math", "credits": 4, "grade": "S"}]
    assert calculate_cgpa(courses)["cgpa"] == 10.0

def test_calculate_cgpa_all_f():
    from utils.vit_engine import calculate_cgpa
    courses = [{"name": "Math", "credits": 4, "grade": "F"}]
    assert calculate_cgpa(courses)["cgpa"] == 0.0

def test_calculate_cgpa_mixed():
    from utils.vit_engine import calculate_cgpa
    courses = [
        {"name": "Math", "credits": 4, "grade": "S"},   # 4*10=40
        {"name": "Physics", "credits": 3, "grade": "B"}, # 3*8=24
    ]
    result = calculate_cgpa(courses)
    assert result["cgpa"] == round(64/7, 2)

# test highlight_matches
def test_highlight_matches_no_matches():
    from utils.regex_engine import highlight_matches
    result = highlight_matches(r"\d+", "no digits here")
    assert "match" not in result.lower() or "<mark>" not in result

def test_highlight_matches_with_match():
    from utils.regex_engine import highlight_matches
    result = highlight_matches(r"\d+", "abc 123 def")
    assert "<mark" in result

def test_highlight_matches_invalid_regex():
    from utils.regex_engine import highlight_matches
    result = highlight_matches(r"[invalid", "test")
    assert "Invalid" in result or "invalid" in result.lower()

# test validate_gemini_key
def test_validate_gemini_key_valid():
    from utils.security_utils import validate_gemini_key
    assert validate_gemini_key("AIza" + "x" * 35) == True

def test_validate_gemini_key_short():
    from utils.security_utils import validate_gemini_key
    assert validate_gemini_key("AIzaShort") == False

def test_validate_gemini_key_wrong_prefix():
    from utils.security_utils import validate_gemini_key
    assert validate_gemini_key("BAAD" + "x" * 35) == False

# test deduplicate_articles
def test_deduplicate_articles_same_url():
    from new_features import deduplicate_articles
    articles = [{"url": "https://example.com/1", "title": "Article 1"}] * 3
    assert len(deduplicate_articles(articles)) == 1

def test_deduplicate_articles_similar_titles():
    from new_features import deduplicate_articles
    articles = [
        {"url": "https://a.com", "title": "AI breakthrough announced today worldwide"},
        {"url": "https://b.com", "title": "AI breakthrough announced today everywhere"},
    ]
    # Similar enough to deduplicate
    result = deduplicate_articles(articles)
    assert len(result) <= 2  # Implementation may or may not dedup these

# test add_medical_disclaimer
def test_medical_disclaimer_added():
    from new_features import add_medical_disclaimer
    result = add_medical_disclaimer("Some medical info.")
    assert "EDUCATIONAL" in result or "educational" in result.lower()

def test_medical_disclaimer_not_duplicated():
    from new_features import add_medical_disclaimer
    text = "Some medical info."
    once = add_medical_disclaimer(text)
    twice = add_medical_disclaimer(once)
    assert twice.count("EDUCATIONAL") <= once.count("EDUCATIONAL") + 1
```

---

## SECTION G — FINAL PRODUCTION CHECKLIST

Before marking complete, verify ALL items:

**AI & API:**
- [ ] OmniKeyEngine waits properly when all keys rate-limited (FIX-OMK-1)
- [ ] Global lock released before HTTP request (FIX-OMK-2)
- [ ] Real token counts parsed from usageMetadata (FIX-OMK-3)
- [ ] Streaming fallback word-tokenizes full response (FIX-OMK-4)
- [ ] SSL uses certifi bundle, not global override (FIX-OMK-5)
- [ ] json_generate() validates JSON and retries with strict prompt
- [ ] batch_generate() uses ThreadPoolExecutor with max_workers=3
- [ ] All ENGINE_PROMPTS entries present (17+ entries total)

**Features:**
- [ ] Flashcard battle mode timer uses JS countdown (no time.sleep)
- [ ] Three-tier answer scoring in battle mode
- [ ] Quiz two-phase pattern (never auto-advance)
- [ ] Quiz bounds check prevents IndexError
- [ ] Essay generation chunks for >2000 word requests
- [ ] Essay originality check renders scorecard
- [ ] Debugger wraps code in XML tags (no backtick breakage)
- [ ] Debugger runs ast.parse() for Python syntax check
- [ ] Debugger diff view color-coded HTML
- [ ] Interview mock mode has full conversation history
- [ ] Salary negotiation strategy generated
- [ ] Company research brief generated
- [ ] Legal jurisdiction selector works
- [ ] Medical disclaimer on EVERY medical AI response
- [ ] Stock dashboard permanent non-dismissible disclaimer
- [ ] Dictionary uses DictionaryAPI.dev first (free, no key)
- [ ] HTML builder validates against arbitrary Tailwind classes
- [ ] PDF uses chunk-based RAG for large documents
- [ ] YouTube has timestamp-linked Q&A
- [ ] Web scraper checks robots.txt
- [ ] VIT CGPA calculator complete with credit planner
- [ ] Pomodoro timer JS countdown, no time.sleep()
- [ ] Regex tester live highlighting on every keystroke
- [ ] Citation generator supports all 7 styles + BibTeX + RIS export
- [ ] Notes engine has #tag system and related notes

**Security:**
- [ ] All API keys validated on startup
- [ ] Key masking in all log output
- [ ] Input sanitization on all text inputs
- [ ] No hardcoded API keys anywhere in codebase
- [ ] Error log accessible via sidebar (collapsed, hidden from normal view)

**UI/UX:**
- [ ] All columns layouts work on 375px mobile screen
- [ ] Feedback (👍/👎) row under every AI output
- [ ] Download button under every text output
- [ ] Descriptive spinner messages (not "Loading…")
- [ ] Session state initialized in init_state() with correct types
- [ ] Emergency reset button in sidebar with confirmation
- [ ] API pool health shown as 🟢/🟡/🔴 traffic light

**Performance:**
- [ ] sympy lazy imported inside math solver function
- [ ] radon lazy imported inside complexity analyzer
- [ ] PIL lazy imported inside image handlers
- [ ] All AI results cached by input hash in session state
- [ ] Images resized to ≤1024px before sending to Gemini Vision
- [ ] No time.sleep() > 0.1s in Streamlit main thread

**Testing:**
- [ ] All unit tests in SECTION F pass without network calls
- [ ] No test uses a real API key
- [ ] Tests cover: validate_cards, calculate_cgpa, highlight_matches, validate_gemini_key, deduplicate_articles, add_medical_disclaimer

---

## SECTION H — IMPLEMENTATION ORDER

Execute in this exact order to minimize dependency errors:

1. `utils/security_utils.py` — No dependencies, needed by everything
2. `utils/secret_manager.py` — Needed by omnikey_engine
3. `utils/omnikey_engine.py` — Core engine, needed by ai_engine
4. `utils/ai_engine.py` — Needed by all feature engines
5. `utils/prompts.py` — Needed by all feature engines
6. `utils/vit_engine.py` — No AI dependencies, pure logic
7. `utils/regex_engine.py` — Uses ai_engine
8. `utils/notes_engine.py` — Uses ai_engine
9. `utils/citation_engine.py` — Uses ai_engine
10. `utils/pdf_handler.py` — Uses fitz, no ai_engine dependency
11. `utils/web_handler.py` — Uses requests/BS4, no ai_engine
12. `utils/youtube_handler.py` — Uses youtube-transcript-api, ai_engine
13. `utils/flashcard_engine.py` — Uses ai_engine
14. `utils/quiz_engine.py` — Uses ai_engine
15. `utils/essay_engine.py` — Uses ai_engine
16. `utils/debugger_engine.py` — Uses ai_engine
17. `utils/interview_engine.py` — Uses ai_engine
18. `utils/analytics.py` — Uses plotly, session state
19. `new_features.py` — Uses all elite engines
20. `advanced_features.py` — Uses all utility engines
21. `app.py` — Main entry, uses everything
22. `tests/test_v5_suite.py` — Tests everything

---

## SECTION I — STYLE & GLASSMORPHISM CSS REFERENCE

Use this CSS for consistent glassmorphism styling across all new UI components:

```css
/* Glass card */
.glass-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 20px;
}

/* Accent colors */
--primary: #a78bfa;    /* Purple */
--success: #4ade80;    /* Green */
--warning: #facc15;    /* Yellow */
--danger:  #f87171;    /* Red */
--muted:   #94a3b8;    /* Gray-blue */

/* Gradient buttons */
.gradient-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
}
```

In Streamlit, inject via:
```python
st.markdown(f'<style>{css_string}</style>', unsafe_allow_html=True)
```

---

## SECTION J — WHAT NOT TO DO (ANTI-PATTERNS)

**DO NOT:**
- Use `st.experimental_rerun()` (deprecated — use `st.rerun()`)
- Use `time.sleep()` > 0.1s in Streamlit main thread
- Use mutable default arguments: `def f(items=[])` is FORBIDDEN
- Import heavy libraries at module level (sympy, radon, PIL in feature files)
- Access `st.session_state["key"]` without guaranteeing key exists first
- Call `st.rerun()` inside `st.spinner()` context
- Use `st.columns(4)` or more on content that wraps on mobile
- Hardcode any API keys (use `st.secrets`)
- Catch `Exception` and silently pass (always log or display the error)
- Use `ssl._create_unverified_context` globally
- Return a stub with a comment like `# implement this later`
- Write `# TODO: ...` anywhere in the production code
- Use `raise NotImplementedError` in any non-abstract method

**ALWAYS:**
- Wrap every AI call in try/except with human-readable error
- Show `st.spinner()` with descriptive verb for every API call > 1s
- Initialize session state in `init_state()` before first access
- Cache AI results by input hash
- Sanitize text inputs before sending to AI
- Mask API keys before logging
- Lazy-import heavy libraries inside functions

---

## CLOSING CONTRACT

You have read the complete specification. You understand the architecture.
You know every free API to use and where. You know every anti-pattern to avoid.
You know the implementation order.

Now write the code. Complete files only. No stubs. No TODOs.
The brain has done its work. The execution is yours.

Start with `utils/security_utils.py` and work down the list in Section H.
Each file you produce must be a complete, runnable Python file.

**Total files to produce: 22 core files + 1 test file = 23 files.**
**Total estimated lines: ~12,000–15,000 lines of production Python.**
**Quality bar: Production-grade. Zero compromises.**

# ════════════════════════════════════════════════════════════════════════════════
# END OF MASTER PROMPT — ExamHelp AI v5.0
# Brain: Claude | Execution: Gemini 2.5 Pro
# ════════════════════════════════════════════════════════════════════════════════
