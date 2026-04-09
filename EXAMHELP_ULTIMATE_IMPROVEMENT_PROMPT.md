# ═══════════════════════════════════════════════════════════════════════════════
# EXAMHELP AI v5.0 — ULTIMATE FEATURE IMPROVEMENT MASTER PROMPT
# Complete Engineering Spec: Every Feature, 100% Robust, Production-Grade
# ═══════════════════════════════════════════════════════════════════════════════
#
# INSTRUCTIONS FOR THE AI ENGINEER / CODE AGENT:
# Read this entire document before writing a single line of code.
# Every section is a contract — implement it fully, not partially.
# Treat every "MUST", "SHALL", and "REQUIRED" as a hard requirement.
# No placeholders. No "TODO" comments. No stubs. Everything is complete.
# ═══════════════════════════════════════════════════════════════════════════════

---

## SECTION 0 — GLOBAL PHILOSOPHY & CONSTRAINTS

You are upgrading ExamHelp AI, a production Streamlit application powered by
Google Gemini via a 9-key rotation pool (OmniKeyEngine). The stack is:
  - Backend: Python 3.12 + Streamlit
  - AI: Gemini 2.5 Flash via `utils/ai_engine.py → generate()` and `generate_stream()`
  - Key rotation: `utils/omnikey_engine.py` (OmniKeyEngine singleton)
  - Prompt config: `utils/prompts.py` (ENGINE_PROMPTS dict)
  - UI: Glassmorphism CSS, Plotly charts, Streamlit native widgets

### Global Rules (apply to every single feature):

RULE-G1: Every AI call MUST have a `try/except` wrapper. On failure, display a
  styled error card — NEVER a raw Python traceback. Error message must be
  human-readable and suggest a retry action.

RULE-G2: Every AI call that takes >1 second MUST show a `st.spinner()` with a
  descriptive message (not just "Loading..."). Use verbs: "Analyzing…",
  "Generating…", "Solving…".

RULE-G3: Every feature that returns text output MUST provide a copy/download
  button immediately below the result. Use `st.download_button()` for text
  files and `pyperclip` is NOT available — use `st.code()` block as the
  copy-friendly fallback.

RULE-G4: Every input widget MUST have a `placeholder` or `help` parameter
  showing the user exactly what to type/upload.

RULE-G5: All session state keys MUST be initialized in `app.py::init_state()`
  with correct default types. Never access `st.session_state["key"]` without
  guaranteeing it exists first.

RULE-G6: Every feature with an AI output MUST include a ⭐ feedback row
  (thumbs up / thumbs down) below the result. Store feedback in
  `st.session_state["feedback_log"]` as a list of dicts.

RULE-G7: Every feature tab MUST render correctly on mobile screens (max-width
  640px). Use `st.columns([1,1])` instead of `st.columns(4)` when the
  content count is ≤2. Use percentage-width CSS, not fixed-pixel widths.

RULE-G8: Temperature and max_tokens for every AI call MUST come from
  `utils/prompts.py::ENGINE_PROMPTS`. Never hardcode these values inline in
  feature files.

RULE-G9: All user-facing text MUST be spell-checked and grammatically
  correct. Remove all placeholder text like "coming soon", "TODO", or
  "WIP" from the UI.

RULE-G10: Every feature that uses an external API (news, stocks, maps, YouTube)
  MUST implement local caching with a configurable TTL stored in session state.
  Default TTL: 600 seconds (10 min). Display last-updated timestamp.

---

## SECTION 1 — CORE AI ENGINE (`utils/ai_engine.py` + `utils/omnikey_engine.py`)

### 1.1 — OmniKeyEngine Critical Fixes

PROBLEM-1: When all 9 keys are simultaneously rate-limited, the engine raises
  RuntimeError immediately instead of waiting up to MAX_WAIT_FOR_KEY seconds.
  The `tried_this_round` set is never reset between polling loops, causing
  instant failure instead of patient waiting.

FIX-1: In `OmniKeyEngine._select_key()`, after a full sweep finds no available
  key, reset `tried_this_round = set()` and sleep 3 seconds before the next
  sweep. Continue until `time.monotonic() - wait_start >= MAX_WAIT_FOR_KEY`.
  Only then raise the rate-limit error.

PROBLEM-2: The global selection lock (`_select_lock`) prevents concurrent
  threads from grabbing the same key but also serializes ALL requests, creating
  a bottleneck under load.

FIX-2: Hold `_select_lock` only for the key selection phase (reading/writing
  the KeySlot). Release the lock before making the actual HTTP request. Use a
  per-key lock (`KeySlot._lock`) for the HTTP call's RPM window update.

PROBLEM-3: Token counting is not implemented. `total_tokens_in` and
  `total_tokens_out` are incremented with 0 on every call.

FIX-3: Parse the `usageMetadata` field from Gemini's JSON response:
  ```python
  meta = response_json.get("usageMetadata", {})
  tokens_in  = meta.get("promptTokenCount", 0)
  tokens_out = meta.get("candidatesTokenCount", 0)
  slot.mark_success(tokens_in=tokens_in, tokens_out=tokens_out)
  ```

PROBLEM-4: `execute_stream()` yields raw word-chunks but doesn't handle the
  case where Gemini returns the entire response in a single `candidates[0]
  .content.parts[0].text` block (no streaming). The generator exits immediately
  with an empty yield.

FIX-4: After calling the REST endpoint without `?alt=sse`, word-tokenize the
  response manually and yield chunks of `chunk_words` words with a 0.03s sleep
  between chunks to simulate smooth streaming.

PROBLEM-5: SSL context fix (`ssl._create_unverified_context`) is applied
  globally in `app.py`. This disables certificate verification for ALL outbound
  requests, creating a security vulnerability.

FIX-5: Create a custom `ssl.SSLContext` that verifies certificates using the
  `certifi` bundle. Apply it only to the Gemini API urllib requests inside
  `omnikey_engine.py`. Remove the global SSL override from `app.py`.

### 1.2 — ai_engine.py Improvements

ADD-1: Implement `generate_with_retry(prompt, max_retries=3, **kwargs)` — a
  wrapper around `generate()` that retries on `RuntimeError` (but NOT on
  rate-limit errors) with exponential backoff (1s, 2s, 4s). Log each retry.

ADD-2: Implement `batch_generate(prompts: list[str], **kwargs) -> list[str]` —
  sends all prompts concurrently using `concurrent.futures.ThreadPoolExecutor`
  with `max_workers=3` (respect rate limits). Returns results in order.

ADD-3: The `json_generate()` function MUST validate the extracted JSON with
  `json.loads()` before returning it. If parsing fails, retry the call once
  with a stricter system prompt: "Return ONLY a raw JSON object. No text
  before or after it. No markdown. No code fences."

ADD-4: Add `get_token_usage_summary() -> dict` that returns total tokens used
  across all keys from `OMNI_ENGINE.get_status_report()`, formatted as:
  `{"total_in": int, "total_out": int, "estimated_cost_usd": float}`
  (Gemini 2.5 Flash pricing: $0.075 per 1M input tokens, $0.30 per 1M output).

### 1.3 — Prompt Registry (`utils/prompts.py`) Completeness

Every engine used in the codebase MUST have a complete entry in ENGINE_PROMPTS.
The following are currently MISSING or incomplete — add them all:

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
        "5. Output ONLY a valid JSON array of card objects."
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
        "4. Output ONLY a valid JSON array."
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
        "Style: Formal, precise, varied sentence structure. No clichés."
    ),
    "temperature": 0.65,
    "max_tokens": 8192,
}

ENGINE_PROMPTS["debugger"] = {
    "system": (
        "You are a Senior Software Engineer and Security Auditor. "
        "Analyze code for: bugs (logic errors, off-by-one, null refs), "
        "security vulnerabilities (injection, unsafe eval, hardcoded secrets), "
        "performance issues (O(n²) loops, memory leaks, redundant I/O), "
        "and code quality (naming, DRY, SOLID principles). "
        "Output Format:\n"
        "### Bug Report\n"
        "### Security Audit\n"
        "### Performance Analysis\n"
        "### Corrected Code (complete, runnable)\n"
        "### Unit Tests (pytest format, 3+ test cases)"
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
        "Synthesize information from multiple sources with academic rigour. "
        "Structure output as:\n"
        "1. Executive Summary\n"
        "2. Key Findings (with inline citations [Author, Year])\n"
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
        "Each slide must have: title, 3-5 bullet points (max 12 words each), "
        "speaker_notes (2-4 sentences the presenter says), visual_suggestion "
        "(what image/chart to use). "
        "Output as JSON array of slide objects. "
        "Follow McKinsey pyramid principle: conclusion first, evidence second."
    ),
    "temperature": 0.5,
    "max_tokens": 8192,
}

ENGINE_PROMPTS["shopping_analyst"] = {
    "system": (
        "You are a Consumer Research Analyst and Deal Expert. "
        "Analyze products with rigorous comparison criteria: "
        "price-to-value ratio, reliability data, user sentiment analysis, "
        "hidden costs, and alternatives. "
        "Always warn about dark patterns, misleading specs, or inflated 'original' prices. "
        "Structure: Summary Table → Detailed Analysis → Red Flags → Recommendation."
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
        "For pronunciation: provide IPA notation + simple phonetic guide."
    ),
    "temperature": 0.3,
    "max_tokens": 3072,
}

ENGINE_PROMPTS["study_planner"] = {
    "system": (
        "You are an Academic Success Coach and Cognitive Scientist. "
        "Create scientifically-grounded study plans based on spaced repetition, "
        "interleaving, and retrieval practice principles. "
        "Output a day-by-day schedule with: date, topics, techniques, "
        "time allocation, and confidence checkpoints. "
        "Adapt difficulty curve: heavy review → consolidation → light review before exam."
    ),
    "temperature": 0.4,
    "max_tokens": 4096,
}
```

---

## SECTION 2 — FLASHCARD ENGINE (100% Complete Implementation)

### 2.1 — Generation (`utils/flashcard_engine.py`)

PROBLEM: Cards are generated without difficulty distribution enforcement.
  Often all cards come back as "Medium". Topic tags are frequently empty.

FIX-2.1a: Inject explicit distribution into the prompt:
  "Generate exactly {easy}% Easy, {medium}% Medium, {hard}% Hard cards.
  Every card MUST have a non-empty 'topic' field derived from the content."

FIX-2.1b: Add post-generation validation:
  ```python
  def validate_cards(cards: list) -> list:
      required = {"q", "a", "topic", "hint", "difficulty"}
      valid = []
      for c in cards:
          if not isinstance(c, dict): continue
          if not all(k in c for k in required): continue
          if not c["q"].strip() or not c["a"].strip(): continue
          if c["difficulty"] not in ("Easy", "Medium", "Hard"):
              c["difficulty"] = "Medium"
          valid.append(c)
      return valid
  ```

FIX-2.1c: If fewer than 3 valid cards are returned, automatically re-generate
  without user prompting. Show a subtle "Improving quality…" spinner.

### 2.2 — Battle Mode (`advanced_features.py::render_flashcard_battle_mode`)

PROBLEM-A: The timer uses `time.time()` comparison but Streamlit re-runs don't
  happen automatically — the timer display is frozen until user interaction.

FIX-A: Add `st.empty()` placeholder for the timer. Use `time.sleep(0.5)` +
  `st.rerun()` inside a `if remaining > 0:` block to create a live countdown.
  Cap auto-reruns at 1 per second using a session state timestamp guard.

PROBLEM-B: Keyword matching for answer scoring is naive — it fails for
  single-word answers, numerical answers, and answers containing special chars.

FIX-B: Implement three-tier matching:
  1. Exact match (after strip + lowercase): score = 1.0
  2. Numerical match: extract all numbers from both strings, compare sets
  3. Semantic keyword match (current logic): score = match_ratio
  Use `max()` of all three tiers as the final score.

ADD-2.2a: Show a "Mastery Heatmap" at battle end. Use a 7×N grid (7 difficulty
  buckets × N topics). Color cells: green (>80%), yellow (50-80%), red (<50%).
  Render as HTML table with inline styles.

ADD-2.2b: Add a "Power-Up" system: after 3 correct in a row, show a random
  encouragement message and award bonus points (+5). Store lifetime points in
  `st.session_state["battle_lifetime_points"]`.

ADD-2.2c: Export deck to CSV button. File format:
  `Question,Answer,Topic,Difficulty,Hint`. Use `io.StringIO` + `st.download_button`.

### 2.3 — AI Tutor (`render_flashcard_ai_tutor`)

PROBLEM: Context window fills up after 8+ messages, causing increasingly
  poor responses as the oldest turns are the most relevant (the flashcard content).

FIX: Implement sliding window with PINNED system context:
  ```python
  system = f"You are an expert tutor. Flashcard context:\n{context}"
  # Always keep the system context pinned
  # Only include the last 6 user/assistant turns
  recent_history = st.session_state.tutor_messages[-6:]
  ```
  Pass `system=system` directly to `generate()` instead of prepending it to
  the user prompt.

ADD-2.3a: "Explain Like I'm 5" button — reformats the last AI response in
  ultra-simple language with a real-world analogy.

ADD-2.3b: "Generate Practice Problem" button — creates a custom exercise based
  on the currently selected topic and last discussed concept.

---

## SECTION 3 — QUIZ ENGINE (100% Complete Implementation)

### 3.1 — Core Quiz Loop

PROBLEM: `quiz_current` index can exceed `len(quiz_data)` if the user switches
  topics mid-quiz, causing an IndexError crash.

FIX: Add bounds check before every question render:
  ```python
  if st.session_state.quiz_current >= len(st.session_state.quiz_data):
      st.session_state.quiz_current = 0
      st.warning("Quiz reset — question index out of range.")
      st.rerun()
  ```

PROBLEM: After answering, the `st.rerun()` call sometimes fires before the
  feedback is displayed, so users never see "Correct!"/"Incorrect!" messages.

FIX: Use a two-phase pattern:
  Phase 1 (answer submitted): Set `quiz_feedback` dict in session state.
    Show feedback. Show "Next Question →" button.
  Phase 2 (next clicked): Increment `quiz_current`. Clear `quiz_feedback`.
    Call `st.rerun()`.
  Never auto-advance to the next question.

### 3.2 — Adaptive Quiz Mode

ADD-3.2: Implement Adaptive Mode that adjusts difficulty based on performance:
  ```python
  def get_next_question_difficulty(scores: dict, topic: str) -> str:
      topic_scores = scores.get(topic, [])
      if len(topic_scores) < 3:
          return "Medium"
      recent_avg = sum(topic_scores[-3:]) / 3
      if recent_avg > 0.8:
          return "Hard"
      elif recent_avg < 0.4:
          return "Easy"
      return "Medium"
  ```
  Use this to filter `quiz_data` for the next question, prioritizing
  questions the user hasn't answered before.

### 3.3 — Quiz Analytics (`render_quiz_analytics`)

ADD-3.3a: Trend line chart — show accuracy over time using Plotly line chart.
  X-axis: question attempt number. Y-axis: rolling 5-question average accuracy.
  Color: gradient from red to green based on trajectory.

ADD-3.3b: "Weak Spot Driller" — generates 5 new targeted questions on the
  user's worst-performing topic using `json_generate()`. These questions must
  address the specific subtopics the user got wrong (stored in a "missed_concepts"
  list in session state).

ADD-3.3c: PDF Report export. Use `reportlab` (if available) or generate an
  HTML string that the browser can print. Include: score summary, topic
  breakdown, wrong questions with correct answers, personalized study tips.
  Fallback: download as formatted `.txt` file.

---

## SECTION 4 — ESSAY WRITER (100% Complete Implementation)

### 4.1 — Essay Generation (`utils/essay_engine.py`)

PROBLEM: Long essays (>1500 words) are truncated mid-sentence because
  `max_tokens` is set too low (defaults to 4096 tokens ≈ ~3000 words, but
  the system prompt consumes ~300 tokens).

FIX-4.1a: For essays >1000 words requested, set `max_tokens=12288`. Add to
  ENGINE_PROMPTS["essay_writer"]: `"max_tokens": 12288`.

FIX-4.1b: Implement chunked essay generation for very long essays (>2000 words):
  1. Generate outline first (section headers + 1-sentence summaries).
  2. Generate each section independently with the outline as context.
  3. Stitch sections together.
  4. Run a final "coherence pass": ask AI to smooth transitions only.

### 4.2 — Plagiarism Style-Check (`render_essay_power_tools`)

PROBLEM: "Plagiarism check" is currently advertised but not implemented —
  clicking it shows nothing.

FIX-4.2: Implement AI-powered originality check:
  ```
  Prompt: "Analyze the following essay for signs of AI-generated text or 
  plagiarized style. Look for: repetitive sentence structures, generic 
  transitions (furthermore, moreover, in conclusion), unnaturally uniform 
  paragraph lengths, absence of personal voice or specific examples, 
  excessive hedging language. 
  
  Rate each dimension 1-10 (10=most human/original):
  - Voice Authenticity: X/10
  - Structural Variety: X/10  
  - Specificity of Examples: X/10
  - Transition Naturalness: X/10
  - Overall Originality Score: X/10
  
  Then provide 3 specific rewrite suggestions."
  ```
  Display results in a styled scorecard with color-coded metrics.

### 4.3 — Co-Write AI Enhancement

FIX-4.3: The Co-Write AI must maintain continuity with the full existing essay.
  Currently it only receives the last 1000 chars. 

  New approach: Send the FULL existing essay as context (up to 8000 chars) but
  instruct the AI: "Do NOT rewrite what already exists. ONLY write the new
  [section] that comes after the last sentence."

  After generation, show a diff view: left column = what existed, right column
  = new AI addition. Use HTML `<ins>` tags with green background for additions.

---

## SECTION 5 — CODE DEBUGGER (100% Complete Implementation)

### 5.1 — Debugger Engine (`utils/debugger_engine.py`)

PROBLEM: The debugger sends raw code to the AI without sanitization. If code
  contains triple-backticks, the prompt breaks.

FIX-5.1a: Wrap user code in XML tags instead of markdown fences:
  ```python
  prompt = f"""<code language="{language}">
  {user_code}
  </code>
  <error>{error_message or 'No error provided — find bugs proactively.'}</error>
  <expected>{expected_output or 'Not specified'}</expected>"""
  ```

FIX-5.1b: Add static analysis BEFORE sending to AI:
  - Python: run `ast.parse()` to catch syntax errors instantly (no API cost)
  - Report syntax errors immediately with line numbers before AI analysis.

ADD-5.1c: Live Complexity Analyzer using `radon` library (Python):
  - Display Cyclomatic Complexity per function (color-coded: A=green, D+=red)
  - Show Maintainability Index
  - Flag functions with complexity > 10 with a ⚠️ warning

ADD-5.1d: Security Audit Mode — specialized prompt focused ONLY on security:
  OWASP Top 10, injection vulnerabilities, hardcoded secrets detection
  (regex scan for patterns like `password = "`, `api_key = "`),
  unsafe deserialization, and path traversal risks.

ADD-5.1e: Test Generator — generates pytest unit tests for every function
  detected in the code. Tests must include: happy path, edge cases (None,
  empty, max int), and expected exception handling.

### 5.2 — Diff Viewer

ADD-5.2: Render a character-level diff between original and fixed code:
  ```python
  import difflib
  diff = difflib.unified_diff(
      original.splitlines(),
      fixed.splitlines(),
      lineterm="",
      n=3,
  )
  ```
  Render each line: deletions with red background (`#3d1212`), additions with
  green background (`#123d12`), context lines with default background.
  Use `st.code()` with a custom HTML fallback for colored diffs.

---

## SECTION 6 — INTERVIEW COACH (100% Complete Implementation)

### 6.1 — Question Generation

PROBLEM: All interview questions are generic. "Tell me about a time you handled
  conflict" for a Machine Learning Engineer role is not appropriate.

FIX-6.1: Inject role-specific technical depth into the prompt:
  ```
  Role: {role}
  Company: {company} (if provided)
  Interview Type: {type}
  Level: {level} (Junior/Mid/Senior/Staff)
  
  For technical roles: 40% technical questions, 30% system design, 30% behavioural.
  For non-technical roles: 20% role-specific knowledge, 80% behavioural.
  Technical questions must include expected answers with code snippets where relevant.
  ```

### 6.2 — Mock AI Interviewer (`advanced_features.py`)

PROBLEM: Mock interviewer does not maintain conversation context — each response
  is generated independently without memory of previous answers.

FIX-6.2: Implement full conversational interview loop:
  ```python
  system = f"""You are a tough but fair interviewer at {company} for a {role} position.
  You have asked {len(history)//2 + 1} questions so far.
  Rules:
  - Ask ONE follow-up question based on the candidate's last answer.
  - If the answer was vague, probe deeper: "Can you be more specific about..."
  - If the answer was strong, raise the bar: "Interesting. How would you handle X?"
  - After 5 exchanges, provide a detailed evaluation scorecard."""
  ```
  Pass the full `messages` history with each call.

ADD-6.2a: Video Script Generator — given a role and company, generates a
  "Tell Me About Yourself" script (90-second verbal answer optimized for impact).

ADD-6.2b: Salary Benchmark Tool — given role + location + years of experience,
  generates a salary negotiation strategy:
  - Market range (low/median/high) based on AI knowledge
  - Negotiation script (what to say when they make an offer)
  - Red lines (what not to accept)
  - Counter-offer template

ADD-6.2c: Company Research Brief — generates a 1-page research brief on a
  company (culture, recent news angles, likely pain points, questions to ask).

---

## SECTION 7 — RESEARCH ASSISTANT (100% Complete Implementation)

### 7.1 — Multi-Source Synthesis

PROBLEM: Research Assistant generates a single response without distinguishing
  between the user's uploaded context and the AI's internal knowledge.

FIX-7.1a: Always clearly label the information source:
  - "[From Your Document]" for context-derived claims
  - "[AI Knowledge Base]" for AI-generated claims
  - "[Requires Verification]" for claims the AI is less certain about

FIX-7.1b: Add a "Confidence Score" (High/Medium/Low) for each major claim,
  based on whether it's derivable from the uploaded context.

### 7.2 — Citation Graph

ADD-7.2: Citation Network Visualizer — when the user provides a research abstract
  with references, extract all cited works and build a Mermaid.js dependency graph:
  ```
  graph LR
    MainPaper["Your Paper"] --> RefA["Author, 2022"]
    MainPaper --> RefB["Author, 2021"]
    RefA --> FoundationalWork["Author, 2018"]
  ```
  Render with `st.markdown(f"```mermaid\n{diagram}\n```")`.

### 7.3 — Research Gap Analysis

ADD-7.3: Research Gap Finder — given an abstract or research area, generate:
  1. A table of 5+ identified research gaps
  2. For each gap: why it's important, methodology suggestions, difficulty rating
  3. Potential research questions for each gap
  4. A suggested research proposal outline (1 page)

---

## SECTION 8 — PRESENTATION BUILDER (100% Complete Implementation)

### 8.1 — Slide Generation

PROBLEM: Generated slides lack visual hierarchy guidance. All bullet points
  are treated equally important.

FIX-8.1a: Add `highlight` field to each bullet:
  ```json
  {"text": "Revenue grew 40% YoY", "highlight": true}
  ```
  Render highlighted bullets with accent color and bold weight.

FIX-8.1b: Add slide type classification: "Title", "Agenda", "Data", "Quote",
  "Team", "Timeline", "Thank You". Apply different rendering templates per type.

### 8.2 — Speaker Coach

ADD-8.2: Speaker Coach Mode — for each slide, generates:
  - Key verbal transition INTO this slide (what to say as you click)
  - 2-minute timed talking points
  - Likely audience question + model answer
  - "Avoid saying" warnings (filler words, jargon for non-expert audiences)

### 8.3 — AI Image Suggestions

ADD-8.3: Per-slide visual suggestion with Unsplash search query:
  Generate an Unsplash search URL for each slide's visual suggestion:
  ```python
  query = slide["visual_suggestion"].replace(" ", "-")
  url = f"https://unsplash.com/s/photos/{query}"
  ```
  Display as a clickable link so the user can browse royalty-free images.

---

## SECTION 9 — ELITE EXPERT ENGINES (9 Engines — Full Robustness)

### 9.1 — Circuit Solver Pro

PROBLEM: Vision-based circuit analysis fails silently when no image is uploaded.
  The solver proceeds with an empty prompt, wasting an API call and returning
  a generic response.

FIX-9.1a: Add strict upload validation:
  ```python
  if uploaded_file is None:
      st.info("📷 Upload a circuit diagram image to begin analysis.")
      st.stop()
  ```

FIX-9.1b: Add image preprocessing for better OCR/analysis:
  - Convert to grayscale (increases contrast for circuit lines)
  - Increase contrast using PIL ImageEnhance
  - Show the processed image preview before sending to AI

ADD-9.1c: Manual Circuit Input Mode — if no image is available, allow text
  description of the circuit: "Resistor 100Ω in series with capacitor 10µF,
  connected to 12V DC source." Parse this and solve analytically.

ADD-9.1d: LaTeX output toggle — render the solution in LaTeX using
  `st.latex()` for equations like KVL/KCL derivations.

### 9.2 — Advanced Math Solver

PROBLEM: SymPy is imported at the top level, causing a 3-5 second import
  delay even when the user is on a different feature tab.

FIX-9.2a: Lazy import inside the function:
  ```python
  def render_math_solver():
      import importlib
      sp = importlib.import_module("sympy") if "sympy" not in sys.modules else sys.modules["sympy"]
  ```

ADD-9.2b: Graph plotter — after solving, if the expression contains a single
  variable, auto-generate a Plotly line chart of the function over a sensible
  domain. Show turning points and zeros.

ADD-9.2c: Step-by-step LaTeX renderer — parse the AI's step-by-step solution
  and render each step that contains an equation with `st.latex()` instead of
  plain text.

ADD-9.2d: "Check My Work" mode — user inputs their own solution steps, AI
  verifies each step and pinpoints the first error.

### 9.3 — Legal Analyser

PROBLEM: Legal output doesn't distinguish between Indian law, UK law, and US law.
  The same prompt generates advice that mixes jurisdictions incorrectly.

FIX-9.3: Add jurisdiction selector (India / USA / UK / EU / International).
  Prepend to system prompt:
  ```
  Jurisdiction: {jurisdiction}
  Apply ONLY the laws, statutes, and case precedents of {jurisdiction}.
  Do not mix with other legal systems unless explicitly comparing them.
  ```

ADD-9.3a: Case Timeline Generator — given a legal scenario, generate a
  chronological timeline of expected legal proceedings (filing → hearing →
  judgment → appeal), with estimated durations per stage.

### 9.4 — Medical Research Guide

PROBLEM: Medical disclaimer is shown only once at the start. If the user
  scrolls past it and asks a follow-up, there's no reminder.

FIX-9.4: Inject disclaimer into EVERY AI response via a post-processing wrapper:
  ```python
  def add_medical_disclaimer(text: str) -> str:
      disclaimer = "\n\n---\n⚠️ **FOR EDUCATIONAL/RESEARCH USE ONLY. NOT MEDICAL ADVICE. Always consult a qualified healthcare professional.**"
      if disclaimer.strip()[:30] not in text:
          return text + disclaimer
      return text
  ```

ADD-9.4b: Drug Interaction Checker — given two or more drug names, generates
  a structured interaction profile: mechanism, severity (Contraindicated/Major/
  Moderate/Minor), clinical significance, and management recommendation.

### 9.5 — Research Scholar

ADD-9.5: Literature Review Matrix — given a list of paper titles/abstracts,
  generates a comparison matrix as an HTML table:
  Columns = papers, Rows = key attributes (methodology, sample size, findings,
  limitations, year). Export as CSV.

### 9.6 — Technical Project Architect

PROBLEM: Generated project blueprints list technologies but don't explain WHY
  each technology was chosen over alternatives.

FIX-9.6: Require the AI to include a "Tech Decision Log" section:
  ```
  ## Technology Decision Log
  | Decision | Choice | Rejected Alternatives | Reasoning |
  |----------|--------|----------------------|-----------|
  | Database | PostgreSQL | MongoDB, MySQL | ACID compliance required... |
  ```

ADD-9.6a: Mermaid.js Architecture Diagram — auto-generate a system architecture
  diagram from the project description. Always include: client layer, API layer,
  service layer, data layer. Render with `st.markdown("```mermaid\n...\n```")`.

### 9.7 — Elite Stocks Dashboard

PROBLEM: Stock data is entirely AI-generated (hallucinated), with no real data.
  This creates serious risk of users making financial decisions based on fiction.

FIX-9.7 CRITICAL: Add a prominent, permanent disclaimer banner at the TOP of
  the page (not dismissible):
  ```
  🚨 IMPORTANT: All stock data, prices, and analysis shown here are AI-GENERATED 
  ESTIMATES for educational purposes only. This is NOT real financial data. 
  Do NOT make investment decisions based on this tool. 
  For real data, use NSE/BSE official websites or registered financial advisors.
  ```
  Make this banner impossible to miss: red border, large font, sticky position.

FIX-9.7b: Remove any AI-generated specific price targets or "Buy/Sell"
  recommendations. Replace with qualitative analysis only.

### 9.8 — AI Dictionary & Lexicon

ADD-9.8a: Pronunciation guide in IPA + phonetic spelling:
  ```
  IPA: /ˈɛpɪˌtɛm/
  Phonetic: EP-ih-tem
  Rhymes with: system, item
  ```

ADD-9.8b: Word Family Tree — show all morphological relatives:
  root word → prefixed forms → suffixed forms → compound words.
  Render as a Mermaid mindmap.

ADD-9.8c: Word Frequency Meter — indicate how common the word is across
  registers: Academic (▓▓▓░░), Journalism (▓▓░░░), Conversation (▓░░░░).

### 9.9 — HTML Page Builder

PROBLEM: Generated HTML sometimes includes Tailwind classes that require
  the full Tailwind CLI build (e.g., arbitrary values like `w-[342px]`).
  These classes don't work with the CDN version.

FIX-9.9a: Inject this constraint into the system prompt:
  "Use ONLY standard Tailwind utility classes available via CDN Play.
  Do NOT use arbitrary values like `w-[342px]` or `text-[14px]`.
  Do NOT use Tailwind plugins (forms, typography) unless the CDN link is included."

FIX-9.9b: After generation, run a regex scan on the output to detect
  arbitrary value patterns `[...]` and warn the user with a yellow callout.

ADD-9.9c: One-click deploy to Netlify Drop — generate a download button for
  the HTML file, and show instructions: "Drag this file to netlify.com/drop
  for instant free hosting." Display a link to Netlify Drop.

---

## SECTION 10 — SUPPORTING FEATURES (Full Robustness)

### 10.1 — PDF Analyst (`utils/pdf_handler.py`)

PROBLEM: Large PDFs (>50 pages) cause the context window to overflow,
  resulting in poor answers about the end of the document.

FIX-10.1a: Implement intelligent chunking:
  1. Split PDF text into 2000-token chunks with 200-token overlap.
  2. Store chunks in `st.session_state["pdf_chunks"]` list.
  3. On each user question, use keyword matching to find the top 3 most
     relevant chunks (TF-IDF or simple word overlap scoring).
  4. Send only those 3 chunks as context (~6000 tokens max).

FIX-10.1b: Show a PDF metadata panel after upload:
  - Page count, file size, estimated reading time
  - Auto-detected language
  - Table of contents (if extractable from PDF bookmarks)

ADD-10.1c: "Summarize by Chapter" mode — if headings are detected in the PDF
  (via font-size analysis with PyMuPDF or heading patterns), generate a
  separate summary for each chapter/section.

### 10.2 — YouTube Handler (`utils/youtube_handler.py`)

PROBLEM: The transcript fetcher fails on YouTube Shorts (< 60s videos) and
  on videos with only auto-generated captions in other languages.

FIX-10.2a: On `TranscriptsDisabled` exception, display helpful guidance:
  "This video has disabled transcripts. Try: (1) Finding the creator's own
  subtitles on their website (2) Using a browser extension to download captions
  (3) Providing a direct URL to the video's .vtt subtitle file."

FIX-10.2b: Fallback language chain — try English first, then `en-US`, then
  `en-GB`, then auto-generated `a.en`, then the first available language.
  Inform the user which language was used.

ADD-10.2c: Timestamp-linked Q&A — after transcript processing, allow questions
  that return timestamp references: "The answer is at 4:23 — [Jump to 4:23](url)".
  Construct the YouTube URL with `?t=263` (seconds).

### 10.3 — Web Scraper (`utils/web_handler.py`)

PROBLEM: BeautifulSoup extraction often grabs navigation menus, footers, and
  cookie banners as part of "content", polluting the AI context.

FIX-10.3a: Implement content extraction heuristics:
  1. Remove all `<nav>`, `<footer>`, `<header>`, `<aside>`, `<script>`,
     `<style>`, `<form>`, `<button>`, `<iframe>` tags before text extraction.
  2. Find the longest `<article>`, `<main>`, or `<div>` block by character count.
  3. Use that as the primary content source.

FIX-10.3b: Add robots.txt compliance check — before scraping, fetch
  `{domain}/robots.txt` and check if the page is disallowed. If disallowed,
  warn the user and ask confirmation before proceeding.

### 10.4 — Voice (Whisper) Input (`voice/input.py`)

PROBLEM: Audio recording is done via `st.audio_input()` but transcription via
  Groq Whisper only. If Groq is unavailable, the entire voice feature fails.

FIX-10.4: Add Gemini Audio fallback:
  ```python
  try:
      result = transcribe_audio(audio_bytes)  # Groq
  except Exception:
      result = transcribe_via_gemini(audio_bytes)  # Fallback
  ```

ADD-10.4b: Auto-submit toggle — if enabled, automatically submits the
  transcribed text to the chat after 1.5 seconds (allows user to see the
  transcription first). If disabled, shows the transcription in an editable
  text input before sending.

### 10.5 — Smart Notes (`utils/notes_engine.py`)

ADD-10.5a: Note Tagging System — user can add #tags to notes.
  Store tags in `st.session_state["note_tags"]` dict mapping tag → [note_indices].
  Show a tag cloud sidebar for filtering notes.

ADD-10.5b: Note Linking — detect when two notes share ≥3 common keywords
  and show a "Related Notes" section at the bottom of each note view.

ADD-10.5c: AI Note Enhancement — one-click button that:
  1. Expands bullet points into full sentences
  2. Adds definitions for technical terms in parentheses
  3. Suggests 3 follow-up questions the note raises

### 10.6 — Citation Generator (`render_citation_generator` in `advanced_features.py`)

PROBLEM: Citation generator is listed as a feature but produces inconsistent
  formatting. APA 7th edition, MLA 9th edition, and Chicago 17th edition have
  different rules for DOI formatting, author name order, and date placement.

FIX-10.6: Add a style selector with 7 formats:
  - APA 7th Edition
  - MLA 9th Edition
  - Chicago 17th (Notes & Bibliography)
  - Chicago 17th (Author-Date)
  - IEEE
  - Harvard
  - Vancouver (medical)

  For each style, create a dedicated system prompt with exact formatting rules.
  Include example output in the prompt so the AI learns the exact format.

ADD-10.6b: Bulk Citation Mode — accept a list of URLs or DOIs (one per line)
  and generate citations for all of them in one API call.

ADD-10.6c: Citation Exporter — export generated citations as:
  - `.bib` (BibTeX for LaTeX users)
  - `.ris` (for Zotero/Mendeley)
  - Plain text (for copy-paste)

### 10.7 — Regex Tester (`render_regex_tester` in `advanced_features.py`)

PROBLEM: Current implementation shows the regex field and test string but the
  "Live match highlighting" mentioned in docstring is not implemented.

FIX-10.7: Implement real-time highlighting using Python's `re` module:
  ```python
  import re
  def highlight_matches(pattern: str, text: str) -> str:
      try:
          compiled = re.compile(pattern)
          matches = list(compiled.finditer(text))
          if not matches:
              return f'<span style="color:#9090b8;">{text}</span>'
          result = ""
          last = 0
          for m in matches:
              result += text[last:m.start()]
              result += f'<mark style="background:#facc15;color:#1a1a2e;border-radius:3px;">{m.group()}</mark>'
              last = m.end()
          result += text[last:]
          return result
      except re.error as e:
          return f'<span style="color:#f87171;">Invalid regex: {e}</span>'
  ```
  Update on every keystroke using `st.text_input` with `on_change` callback.

ADD-10.7b: AI Regex Explainer — given a regex pattern, explain every
  component in plain English: `^[a-zA-Z0-9._%+-]+` → "Start of string,
  followed by one or more characters that are letters, digits, or ._%+-"

ADD-10.7c: AI Regex Generator — user describes what they want to match in
  plain English, AI generates the regex pattern with explanation and test cases.

### 10.8 — VIT Academics (`render_vit_academics` in `advanced_features.py`)

PROBLEM: VIT CGPA calculator is listed as "coming soon" despite being in the
  feature list.

FIX-10.8: Implement fully:

  ```python
  def calculate_cgpa(courses: list[dict]) -> dict:
      """
      courses: [{"name": str, "credits": int, "grade": str}]
      VIT Grade Scale: S=10, A=9, B=8, C=7, D=6, E=5, F=0
      """
      grade_map = {"S":10,"A":9,"B":8,"C":7,"D":6,"E":5,"F":0}
      total_credits = sum(c["credits"] for c in courses)
      total_points = sum(c["credits"] * grade_map.get(c["grade"].upper(), 0) for c in courses)
      cgpa = total_points / total_credits if total_credits > 0 else 0
      return {
          "cgpa": round(cgpa, 2),
          "total_credits": total_credits,
          "grade_points": total_points,
          "classification": (
              "First Class with Distinction" if cgpa >= 8.5 else
              "First Class" if cgpa >= 7.5 else
              "Second Class" if cgpa >= 6.0 else
              "Pass"
          )
      }
  ```
  
  Add Credit Planner: show how many credits of S/A grades are needed to
  reach target CGPA. Show the minimum possible improvement scenario.

### 10.9 — Study Toolkit (`render_study_toolkit` in `advanced_features.py`)

PROBLEM: Pomodoro timer uses `time.sleep()` which blocks Streamlit's event loop,
  freezing the entire UI for the duration.

FIX-10.9: Replace with a JavaScript countdown embedded via `st.components.v1.html`:
  ```html
  <script>
  let remaining = {seconds};
  const display = document.getElementById('timer');
  const interval = setInterval(() => {
      remaining--;
      const m = Math.floor(remaining/60).toString().padStart(2,'0');
      const s = (remaining%60).toString().padStart(2,'0');
      display.textContent = m + ':' + s;
      if (remaining <= 0) {
          clearInterval(interval);
          display.textContent = '00:00';
          const audio = new Audio('https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3');
          audio.play().catch(()=>{});
      }
  }, 1000);
  </script>
  <div id="timer" style="font-size:4rem;font-weight:900;color:#a78bfa;text-align:center;">
  {minutes_display}:{seconds_display}
  </div>
  ```

ADD-10.9b: Focus Music Player — embed a curated Spotify/YouTube playlist link
  for study music. Offer 4 options: Lo-Fi Hip-Hop, Classical (Mozart Effect),
  Binaural Beats (40Hz Gamma), and Brown Noise.

ADD-10.9c: Session History — after each Pomodoro completes, log it to
  `st.session_state["pomodoro_log"]` with timestamp and duration. Show a
  weekly activity chart (similar to GitHub contribution graph).

### 10.10 — News Hub (`render_news_hub` in `new_features.py`)

PROBLEM: `fetch_all_ai_news()` fetches from multiple sources but has no
  deduplication. The same article from Reuters appears 3 times (from 3
  different aggregator feeds).

FIX-10.10a: Deduplicate by URL AND by title similarity:
  ```python
  def deduplicate_articles(articles: list) -> list:
      seen_urls = set()
      seen_titles = []
      unique = []
      for article in articles:
          url = article.get("url", "")
          title = article.get("title", "").lower()[:50]
          if url in seen_urls:
              continue
          # Simple title similarity: check if any seen title shares >60% words
          title_words = set(title.split())
          is_dup = any(
              len(title_words & set(t.split())) / max(len(title_words), 1) > 0.6
              for t in seen_titles
          )
          if not is_dup:
              seen_urls.add(url)
              seen_titles.append(title)
              unique.append(article)
      return unique
  ```

ADD-10.10b: Article Summarizer — one-click "Summarize" button per article
  card that fetches the article URL content (using `requests.get` with a
  10-second timeout and `newspaper3k` for content extraction) and summarizes
  it in 3 bullet points.

---

## SECTION 11 — UI/UX GLOBAL IMPROVEMENTS

### 11.1 — Sidebar

FIX-11.1a: The API Pool Status display currently shows raw technical data
  (key aliases, cooldown seconds). Replace with a simplified dashboard:
  - Overall health: 🟢 All Systems Go / 🟡 Reduced Capacity / 🔴 Degraded
  - Available keys: X/9
  - Estimated wait time: "Ready now" or "Next key available in Xs"
  - Token usage today: X,XXX tokens (X% of daily estimate)

FIX-11.1b: Persona selector must show a PREVIEW of each persona when hovered.
  Use `st.selectbox` with a `help` parameter containing the persona description.

ADD-11.1c: "Emergency Reset" button in sidebar — resets ALL session state
  except API keys. Useful when the app gets into a broken state. Add
  confirmation dialog: "This will clear all your current session data. Continue?"

### 11.2 — Main Chat Interface

FIX-11.2a: Message streaming via `generate_stream()` must handle interruption
  gracefully. If the user navigates away mid-stream, the remaining stream
  tokens must be discarded cleanly (not cached to session state).

FIX-11.2b: Code blocks inside chat messages must have syntax highlighting.
  Use `st.code(block, language=detected_lang)` or detect language from the
  opening fence ` ```python `.

ADD-11.2c: Reaction system on every message — allow 👍 👎 📌 (bookmark) 🔄
  (regenerate). "Regenerate" re-sends the last user message and replaces
  the assistant message.

### 11.3 — Analytics Dashboard (`utils/analytics.py`)

FIX-11.3a: Subject mastery radar chart fails when there are <3 subjects.
  Plotly radar charts require ≥3 axes. Add minimum 3-axis enforcement:
  ```python
  if len(subjects) < 3:
      subjects += ["Other"] * (3 - len(subjects))
      scores += [0] * (3 - len(scores))
  ```

ADD-11.3b: Daily Study Streak tracker — calculate the streak from
  `st.session_state["session_dates"]` (a list of date strings). Show
  streak as a fire counter: 🔥 7-day streak! Display a calendar heatmap
  for the last 30 days.

ADD-11.3c: Export analytics as PDF — generate a weekly report card with:
  radar chart, streak, topics studied, questions answered, accuracy trend.

---

## SECTION 12 — SECURITY & CONFIGURATION HARDENING

### 12.1 — API Key Security

PROBLEM: `utils/secret_manager.py` loads keys via `st.secrets` which is
  correct, but there's no validation of key format before using them.

FIX-12.1a: Validate all keys on startup:
  ```python
  def validate_gemini_key(key: str) -> bool:
      return (
          isinstance(key, str) and
          key.startswith("AIza") and
          len(key) == 39
      )
  ```
  Log warnings for malformed keys. Skip invalid keys entirely.

FIX-12.1b: Implement key masking in all log output:
  ```python
  def mask_key(key: str) -> str:
      return key[:6] + "..." + key[-4:] if len(key) > 10 else "***"
  ```
  Never log a full API key. Search entire codebase for `print(key)` and
  replace with `print(mask_key(key))`.

### 12.2 — Input Sanitization

FIX-12.2: All text inputs that are sent to the AI MUST be sanitized:
  1. Strip leading/trailing whitespace
  2. Limit to configured max length (default: 10,000 chars)
  3. Remove null bytes: `text.replace('\x00', '')`
  4. Warn user if input exceeds the limit instead of silently truncating

### 12.3 — Error Logging

ADD-12.3: Implement centralized error logger:
  ```python
  # utils/error_logger.py
  import datetime
  def log_error(feature: str, error: Exception, context: dict = None):
      entry = {
          "timestamp": datetime.datetime.utcnow().isoformat(),
          "feature": feature,
          "error_type": type(error).__name__,
          "error_msg": str(error)[:500],
          "context": context or {}
      }
      if "error_log" not in st.session_state:
          st.session_state["error_log"] = []
      st.session_state["error_log"].append(entry)
  ```
  Add a "View Error Log" section in sidebar (collapsed by default) for debugging.

---

## SECTION 13 — PERFORMANCE OPTIMIZATIONS

### 13.1 — Lazy Loading

FIX-13.1: Move all heavy imports inside the function that uses them.
  Currently banned from module-level imports (unless already there):
  - `sympy` (math solver)
  - `radon` (complexity analyzer)
  - `plotly` (only import when chart is rendered)
  - `PIL` (only import when image is uploaded)
  - `pdfplumber` / `pypdf` (only import when PDF is uploaded)
  - `newspaper3k` (only import for article summarization)

### 13.2 — Session State Caching

FIX-13.2: Every AI-generated result MUST be cached in session state with a
  cache key based on the input. Before calling the AI, check the cache:
  ```python
  cache_key = f"result_{feature_name}_{hashlib.md5(input_text.encode()).hexdigest()[:8]}"
  if cache_key in st.session_state:
      result = st.session_state[cache_key]
  else:
      result = generate(...)
      st.session_state[cache_key] = result
  ```

### 13.3 — Image Optimization

FIX-13.3: Before sending images to Gemini Vision, resize them:
  ```python
  from PIL import Image
  import io
  def optimize_image(img_bytes: bytes, max_dim: int = 1024) -> bytes:
      img = Image.open(io.BytesIO(img_bytes))
      img.thumbnail((max_dim, max_dim), Image.LANCZOS)
      output = io.BytesIO()
      img.save(output, format="JPEG", quality=85, optimize=True)
      return output.getvalue()
  ```
  This reduces token consumption by up to 70% for high-resolution images.

---

## SECTION 14 — TESTING REQUIREMENTS

### 14.1 — Unit Tests (`test_stress.py` — Expand)

ADD tests for the following:
  1. `validate_cards()` — test with missing fields, wrong types, empty strings
  2. `calculate_cgpa()` — test with all S grades, all F grades, mixed grades
  3. `highlight_matches()` — test with no matches, multiple matches, nested groups
  4. `validate_gemini_key()` — test with valid key, short key, wrong prefix
  5. `deduplicate_articles()` — test with identical URLs, similar titles, unique articles
  6. `add_medical_disclaimer()` — test it's added once, not duplicated

### 14.2 — Integration Test (`test_omnikey_live.py` — Expand)

ADD tests for:
  1. All-keys-rate-limited scenario — mock 9 keys all in cooldown, verify
     engine waits and doesn't crash immediately
  2. Concurrent requests — send 5 simultaneous `generate()` calls, verify
     no two requests use the same key simultaneously
  3. Invalid key graceful handling — one key returns 401, verify it's
     marked INVALID and not retried

---

## SECTION 15 — FINAL INTEGRATION CHECKLIST

Before marking this upgrade complete, verify ALL of the following:

☐ Every feature renders without error with empty inputs (edge case: user
  clicks "Generate" without typing anything)
☐ Every feature renders without error when the AI returns an empty string
☐ Every feature renders without error when the AI raises an exception
☐ No `st.rerun()` is called inside a `st.spinner()` context (causes double-render)
☐ No mutable default arguments in any function (`def f(items=[])` is forbidden)
☐ No `time.sleep()` > 0.1s in the Streamlit main thread
☐ All `st.columns()` calls have consistent column counts per screen breakpoint
☐ The sidebar API status shows real data, not mocked data
☐ All download buttons produce files that actually open correctly
☐ The Pomodoro timer counts down in real-time without freezing the UI
☐ The regex tester highlights matches in real-time as the user types
☐ Battle mode timer auto-advances when time runs out
☐ Medical disclaimer appears on every medical AI response
☐ Stock disclaimer is permanent and cannot be dismissed
☐ All citation formats are correctly formatted per their style guides
☐ PDF chunking prevents context overflow for documents > 50 pages
☐ YouTube Q&A returns timestamp links when applicable
☐ The VIT CGPA calculator produces correct results for known inputs
☐ Error logs are accessible but hidden from normal users
☐ No full API keys appear in any log output or error message
☐ All images sent to Gemini are resized to ≤ 1024px on the longest side
☐ All heavy libraries are lazy-loaded inside functions, not at module level
☐ Session state is fully initialized in `init_state()` with correct types
☐ Every AI response has a feedback (👍/👎) mechanism
☐ Every feature works on a 375px-wide mobile screen

# ═══════════════════════════════════════════════════════════════════════════════
# END OF MASTER IMPROVEMENT PROMPT
# Total: 1,010+ lines of engineering specification
# Implement every requirement above for a fully robust, production-grade system.
# ═══════════════════════════════════════════════════════════════════════════════
