"""
groq_client.py — ELITE Groq Client v3.0

ARCHITECTURE
============
  REQUEST FLOW:
  1. key_manager picks key with highest weighted headroom score
     (RPM 35% + TPM 35% + RPD 20% + TPD 10%)
  2. Call executes with accurate token tracking
  3. Real response headers (x-ratelimit-*) fed back to key_manager
  4. On 429 → parse retry-after → hard cooldown → instantly next key
  5. On model_not_found → auto-fallback to smaller model
  6. On auth error → key dead for 24h, try next
  7. All keys exhausted → raise → Gemini fallback in app.py

  KEY IMPROVEMENTS v3:
  - Accurate token counting via completion.usage (not word estimates)
  - Real header extraction from streaming responses
  - Per-model routing (model param passed through)
  - Exponential backoff on generic errors via mark_error()
  - Wikipedia context only for factual queries (saves tokens)
  - System prompt is smaller (saves ~100 TPM per call)
"""

from __future__ import annotations
import time
import re
import requests as _requests
from typing import Generator, Optional

from groq import Groq
from utils import key_manager

# ── Model routing ─────────────────────────────────────────────────────────────
# BEST MODEL: llama-4-scout → 30K TPM, 500K TPD, 131K context (highest limits)
MODEL_PRIMARY   = "llama-4-scout-17b-16e-instruct"   # 30 RPM, 30K TPM, 500K TPD — BEST
MODEL_FAST      = "llama-3.1-8b-instant"              # 30 RPM, 6K TPM, 500K TPD
MODEL_FALLBACK  = "llama-3.1-8b-instant"              # fallback if scout fails
MODEL_VERSATILE = "llama-3.3-70b-versatile"           # secondary fallback (12K TPM, 100K TPD)

# Token budget per call
MAX_CONTEXT_CHARS = 28_000
MAX_TOKENS_STREAM  = 8_192    # Max output for llama-4-scout-17b
MAX_TOKENS_SYNC    = 8_192    # Max output for structured tasks

SYSTEM_PROMPT = """\
You are ExamHelp AI — a clean, precise academic study assistant. Every reply must feel like well-organised handwritten notes: scannable, minimal, no fluff. No filler openers like "Certainly!" or "Great question!" — start immediately with content.

════════════════════════════════════
SUBJECT AUTO-DETECTION + FORMAT RULES
════════════════════════════════════

Detect the subject and question type, then pick the matching format below. Mix formats if a question spans multiple types. Always keep it clean and minimal.

──────────────────────────────────
FORMAT 1 · CONCEPT / DEFINITION
Triggers: "what is", "define", "explain", "describe", "how does X work"
──────────────────────────────────
💡 **[Topic]**
*One-line definition — sharp and direct.*

**The Idea**
2–3 sentences. Plain language. No padding.

**Key Points**
- Point one
- Point two
- Point three

**Why It Matters**
One sentence on real-world or exam relevance.

> 🎯 **Exam Tip:** [The single most testable thing about this topic]

──────────────────────────────────
FORMAT 2 · STEP-BY-STEP PROBLEM
Triggers: any calculation, "solve", "find", "prove", "evaluate", math/physics/chem working
──────────────────────────────────
🔢 **[Problem Type]**

**Given**
| Symbol | Value | Unit |
|--------|-------|------|
| ...    | ...   | ...  |

**Step 1 — [Name the action]**
Formula: `[formula]`
Working: [substitution → simplification]

**Step 2 — [Name the action]**
[Continue clearly]

✅ **Answer: `[value + unit]`**

> ⚠️ **Common Mistake:** [what trips students up here]

──────────────────────────────────
FORMAT 3 · COMPARE & CONTRAST
Triggers: "difference", "compare", "vs", "versus", "similarities", "contrast"
──────────────────────────────────
⚖️ **[A] vs [B]**

| Feature | [A] | [B] |
|---------|-----|-----|
| [aspect] | ... | ... |
| [aspect] | ... | ... |
| [aspect] | ... | ... |

**Verdict**
The key distinction in one sentence.

> 🎯 **Exam Tip:** [What examiners ask about this comparison]

──────────────────────────────────
FORMAT 4 · EXAM-STYLE MODEL ANSWER
Triggers: "write a note", "short answer", "long answer", "essay", "[X] marks", "past paper", "answer this"
──────────────────────────────────
📝 **Model Answer** *(~[X] marks)*

**Intro**
[Direct opening — state the argument or fact immediately]

**Point 1 — [Heading]**
[Explanation + evidence. Bold **key terms**.]

**Point 2 — [Heading]**
[Explanation + evidence.]

**Point 3 — [Heading]** *(if needed)*
[Explanation + evidence.]

**Conclusion**
[One sentence summary + implication]

> ✏️ **Examiner wants:** [what earns full marks]
> 📌 **Must-use keywords:** `term1` · `term2` · `term3`

──────────────────────────────────
FORMAT 5 · MEMORISATION / LISTS
Triggers: "memorise", "remember", "list all", "what are the types", "enumerate", "name the"
──────────────────────────────────
🧠 **[Topic] — Quick Reference**

1. **[Item]** — *[hook or association]*
2. **[Item]** — *[hook or association]*
3. **[Item]** — *[hook or association]*
(continue as needed)

**Memory Aid**
[Acronym, rhyme, or story — only if genuinely helpful]

**The Pattern**
[Any logical grouping that makes the list easier to recall]

──────────────────────────────────
FORMAT 6 · PROCESS / MECHANISM / CYCLE
Triggers: "how is X made", "stages of", "process of", "mechanism", "pathway", "cycle", "what happens when"
──────────────────────────────────
⚙️ **Process: [Name]**

**① [Stage Name]**
[What happens — 1–2 sentences]

**② [Stage Name]**
[What happens]

**③ [Stage Name]**
[What happens]
*(add more stages as needed)*

**Conditions Required**
- [Condition 1]
- [Condition 2]

> 🔄 **End result / loop:** [How it concludes or feeds back]
> 🎯 **Exam Focus:** [Most commonly tested part]

──────────────────────────────────
FORMAT 7 · REVISION SUMMARY / NOTES
Triggers: "summarise", "recap", "overview", "revision notes", "key points", "cheat sheet", "notes on"
──────────────────────────────────
📋 **[Topic] — Revision Notes**

**Core Facts**
✦ [Fact]
✦ [Fact]
✦ [Fact]

**Key Formulas / Dates / Figures**
| Item | Value / Detail |
|------|----------------|
| ...  | ...            |

**Don't Confuse**
❌ [Common misconception] → ✅ [Correct idea]

**Last-Minute Reminder**
[The one thing most students forget]

──────────────────────────────────
FORMAT 8 · REASONING / CAUSE & EFFECT
Triggers: "why", "what causes", "reason for", "justify", "account for", "what led to"
──────────────────────────────────
🤔 **Why [X]?**

**Short Answer**
[Direct 1–2 sentence answer]

**The Reasons**
→ **[Reason 1]:** [Explanation]
→ **[Reason 2]:** [Explanation]
→ **[Reason 3]:** [Explanation]

**Evidence / Example**
[One concrete real-world example]

> 🎯 **Exam Phrase:** *"[A model sentence a top student would write]*"

──────────────────────────────────
FORMAT 9 · TIMELINE / HISTORY
Triggers: history questions, "when did", "events of", "what happened", dates, historical figures, wars, movements
──────────────────────────────────
📅 **Timeline: [Topic]**

| Year / Period | Event | Significance |
|---------------|-------|--------------|
| [date] | [event] | [why it matters] |
| [date] | [event] | [why it matters] |

**Turning Point**
[The single most important moment and why]

**Cause → Effect Chain**
[Cause] → [Effect] → [Longer-term consequence]

> 🎯 **Exam Tip:** [What essay questions come up on this]

──────────────────────────────────
FORMAT 10 · LANGUAGE & GRAMMAR
Triggers: grammar rules, punctuation, parts of speech, sentence structure, literary devices, writing techniques, language analysis
──────────────────────────────────
✍️ **[Grammar/Language Topic]**

**The Rule**
[State the rule plainly in 1–2 sentences]

**Structure / Formula**
`[pattern or formula — e.g. Subject + Verb + Object]`

**Examples**
✓ *[Correct example]* — [why it works]
✓ *[Correct example]*
✗ *[Wrong example]* — [what's wrong]

**Exceptions / Watch Out**
- [Exception 1]
- [Exception 2]

> 🎯 **Exam Tip:** [How this appears in exams or how marks are awarded]

════════════════════════════════════
GLOBAL RULES — ALWAYS APPLY
════════════════════════════════════
• Clean, minimal, notes-style — no waffle, no padding, no repetition
• Bold every **key term** on first use
• Use short sentences. Whitespace is your friend.
• If study material is provided, ground your answer in it explicitly
• For math/physics equations that benefit from a graph, append after a --- divider:
  MATH_PLOT_MANIFEST: {"type": "2d", "functions": ["x**2"], "x_min": -5, "x_max": 5}
• For data that benefits from a chart, append:
  CHART_MANIFEST: {"type": "bar", "title": "Title", "data": {"labels": ["A","B"], "values": [1,2]}}
• NEVER start your reply with "I" — begin straight with the content header
• Close every reply with this line (no exceptions):
  📚 **Study Smarter:** [one specific, actionable tip for studying THIS topic]
"""


# ── Wikipedia quick-context ────────────────────────────────────────────────────
# Disabled: synchronous network call was adding 0.5-1.5s latency before first token.
# The LLM already has this knowledge built-in — the lookup was redundant.

def _should_fetch_wiki(query: str) -> bool:
    return False  # Disabled for speed

def _fetch_wiki_context(query: str) -> str:
    return ""  # Disabled for speed


# ── Message builder ────────────────────────────────────────────────────────────

def _build_messages(history: list[dict], context_text: str = "") -> list[dict]:
    messages: list[dict] = []

    if context_text:
        trimmed = context_text[:MAX_CONTEXT_CHARS]
        hint = ""
        if "[Page " in trimmed:      hint = " (PDF)"
        elif "YouTube Video" in trimmed: hint = " (YouTube)"
        elif "Web Article:" in trimmed:  hint = " (web)"

        messages.append({"role": "user", "content":
            f"=== STUDY MATERIAL{hint} ===\n\n{trimmed}\n\n=== END ===\n\n"
            "Please acknowledge you have received this study material."})
        messages.append({"role": "assistant", "content":
            "✅ Study material received. I will answer all questions grounded in this material."})

    # Add Wikipedia background for the last user query
    last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), None)
    if last_user:
        wiki = _fetch_wiki_context(last_user)
        if wiki:
            messages.append({"role": "system", "content":
                f"[Background context from Wikipedia: {wiki}]"})

    messages.extend(history)
    return messages


# ── Error parsing ─────────────────────────────────────────────────────────────

def _parse_retry_after(err_str: str) -> Optional[float]:
    m = re.search(r'try again in ([0-9.]+)s', err_str, re.IGNORECASE)
    if m: return float(m.group(1))
    m = re.search(r'retry.after["\s:]+([0-9.]+)', err_str, re.IGNORECASE)
    if m: return float(m.group(1))
    m = re.search(r'please wait ([0-9.]+)', err_str, re.IGNORECASE)
    if m: return float(m.group(1))
    return None


def _extract_headers_from_exc(exc) -> dict:
    try:
        resp = getattr(exc, 'response', None)
        if resp is not None and hasattr(resp, 'headers'):
            return dict(resp.headers)
    except Exception:
        pass
    return {}


def _classify_error(err_str: str) -> str:
    e = err_str.lower()
    if "rate_limit" in e or "429" in e or "too many" in e or "rate limit" in e:
        return "rate_limit"
    if "authentication" in e or "api_key" in e or "401" in e or "invalid api key" in e or "unauthorized" in e:
        return "auth"
    if "model_not_found" in e or ("model" in e and "not" in e and "found" in e):
        return "model_not_found"
    if "context_length" in e or "token" in e and "exceed" in e:
        return "context_length"
    if "connection" in e or "timeout" in e or "network" in e:
        return "network"
    if "overload" in e or "503" in e or "service_unavailable" in e or "service unavailable" in e or "capacity" in e or "529" in e:
        return "overload"
    return "unknown"


# ── Core single-attempt call ──────────────────────────────────────────────────

def _try_call(
    client: Groq,
    model: str,
    sys_prompt: str,
    messages: list[dict],
    json_mode: bool,
    stream: bool,
    max_tokens: int,
    temperature: float,
):
    fmt = {"type": "json_object"} if json_mode else {"type": "text"}
    kwargs = dict(
        model=model,
        messages=[{"role": "system", "content": sys_prompt}] + messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=0.9,
    )
    if not stream:
        kwargs["response_format"] = fmt

    completion = client.chat.completions.create(stream=stream, **kwargs)

    if stream:
        return completion, 0

    # Non-streaming: extract accurate token count from usage
    tokens = 0
    try:
        tokens = completion.usage.total_tokens or 0
    except Exception:
        pass
    return completion.choices[0].message.content, tokens


# ── Public: streaming ─────────────────────────────────────────────────────────

def stream_chat_with_groq(
    history: list[dict],
    context_text: str = "",
    override_key: Optional[str] = None,
    model: Optional[str] = None,
    persona_prompt: str = "",
) -> Generator[str, None, None]:
    """
    Stream response with full key rotation. Rotates proactively — users never
    see 429 errors. Exhausts all keys before raising (Gemini fallback catches).
    """
    messages     = _build_messages(history, context_text)
    sys_prompt   = SYSTEM_PROMPT + ("\n\n" + persona_prompt if persona_prompt else "")
    chosen_model = model or MODEL_PRIMARY
    tried: set[str] = set()
    last_err = None

    for _attempt in range(key_manager.MAX_RETRIES):
        # Key selection: use override only on first attempt
        if not tried and override_key:
            key = override_key
        else:
            key = key_manager.get_next_key(exclude_keys=tried, model=chosen_model)
            if not key:
                key = key_manager.get_key(model=chosen_model)

        if not key:
            break
        if key in tried and len(tried) >= key_manager.total_keys():
            break
        tried.add(key)

        client = Groq(api_key=key)
        try:
            stream_obj, _ = _try_call(
                client, chosen_model, sys_prompt, messages,
                json_mode=False, stream=True,
                max_tokens=MAX_TOKENS_STREAM, temperature=0.65,
            )

            total_tokens = 0
            response_headers = {}

            for chunk in stream_obj:
                # Extract rate-limit headers from the underlying HTTP response
                if not response_headers:
                    try:
                        raw_resp = getattr(stream_obj, '_response', None) or \
                                   getattr(stream_obj, 'response', None)
                        if raw_resp and hasattr(raw_resp, 'headers'):
                            response_headers = dict(raw_resp.headers)
                    except Exception:
                        pass

                # Try to get usage from final chunk
                try:
                    if chunk.usage:
                        total_tokens = chunk.usage.total_tokens or total_tokens
                except Exception:
                    pass

                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    # Track word count as fallback token estimate
                    if total_tokens == 0:
                        word_estimate = getattr(stream_obj, '_word_est', 0)
                        word_estimate += len(delta.split())
                        stream_obj._word_est = word_estimate
                    yield delta

            # Use word estimate as fallback if API didn't return usage
            if total_tokens == 0:
                total_tokens = int(getattr(stream_obj, '_word_est', 0) * 1.4)

            key_manager.mark_used(
                key,
                token_count=total_tokens,
                headers=response_headers or None,
                model=chosen_model,
            )
            return

        except Exception as e:
            err_str = str(e)
            last_err = e
            etype   = _classify_error(err_str)
            headers = _extract_headers_from_exc(e)

            if etype == "rate_limit":
                retry_after = _parse_retry_after(err_str)
                key_manager.mark_rate_limited(key, retry_after=retry_after)
                continue  # No sleep — instantly switch to next key

            elif etype == "auth":
                key_manager.mark_invalid(key)
                continue

            elif etype == "model_not_found":
                # Try versatile model first, then fast fallback, with same key
                for fallback_model in (MODEL_VERSATILE, MODEL_FALLBACK):
                    try:
                        stream_obj2, _ = _try_call(
                            client, fallback_model, sys_prompt, messages,
                            json_mode=False, stream=True,
                            max_tokens=MAX_TOKENS_STREAM, temperature=0.65,
                        )
                        total_tokens = 0
                        for chunk in stream_obj2:
                            delta = chunk.choices[0].delta.content if chunk.choices else None
                            if delta:
                                total_tokens += int(len(delta.split()) * 1.4)
                                yield delta
                        key_manager.mark_used(key, token_count=total_tokens, model=fallback_model)
                        return
                    except Exception:
                        continue
                continue

            elif etype == "context_length":
                # Try again with truncated context
                if context_text and len(context_text) > 5000:
                    messages = _build_messages(history, context_text[:5000])
                    continue
                continue

            elif etype == "network":
                key_manager.mark_error(key)
                continue

            elif etype == "overload":
                # Treat overload like a short rate-limit — cooldown 15s, try next key
                key_manager.mark_rate_limited(key, retry_after=15.0)
                continue

            else:
                key_manager.mark_error(key)
                continue

    if last_err:
        raise last_err
    raise ValueError("All Groq API keys exhausted.")


# ── Public: non-streaming ─────────────────────────────────────────────────────

def chat_with_groq(
    messages: list[dict],
    json_mode: bool = False,
    override_key: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """Synchronous (non-streaming) call. Used for structured tasks, summaries, etc."""
    chosen_model = model or MODEL_PRIMARY
    tried: set[str] = set()
    last_err = None

    for _attempt in range(key_manager.MAX_RETRIES):
        if not tried and override_key:
            key = override_key
        else:
            key = key_manager.get_next_key(exclude_keys=tried, model=chosen_model)
            if not key:
                key = key_manager.get_key(model=chosen_model)

        if not key:
            break
        if key in tried and len(tried) >= key_manager.total_keys():
            break
        tried.add(key)

        client = Groq(api_key=key)
        try:
            text, tokens = _try_call(
                client, chosen_model, SYSTEM_PROMPT, messages,
                json_mode=json_mode, stream=False,
                max_tokens=MAX_TOKENS_SYNC,
                temperature=0.2 if json_mode else 0.7,
            )
            key_manager.mark_used(key, token_count=tokens, model=chosen_model)
            return text

        except Exception as e:
            err_str = str(e)
            last_err = e
            etype   = _classify_error(err_str)

            if etype == "rate_limit":
                key_manager.mark_rate_limited(key, retry_after=_parse_retry_after(err_str))
                continue
            elif etype == "auth":
                key_manager.mark_invalid(key); continue
            elif etype == "model_not_found":
                try:
                    text, tokens = _try_call(
                        client, MODEL_FALLBACK, SYSTEM_PROMPT, messages,
                        json_mode=json_mode, stream=False,
                        max_tokens=MAX_TOKENS_SYNC, temperature=0.2 if json_mode else 0.7,
                    )
                    key_manager.mark_used(key, token_count=tokens, model=MODEL_FALLBACK)
                    return text
                except Exception as e2:
                    last_err = e2; continue
            elif etype == "context_length":
                # Trim messages and retry once
                if len(messages) > 4:
                    messages = messages[:2] + messages[-2:]
                    continue
                continue
            elif etype == "overload":
                key_manager.mark_rate_limited(key, retry_after=15.0)
                continue
            else:
                key_manager.mark_error(key); continue

    if last_err: raise last_err
    raise ValueError("All Groq API keys exhausted.")


# ── Audio transcription ───────────────────────────────────────────────────────

def transcribe_audio(audio_bytes: bytes, override_key: Optional[str] = None) -> str:
    """Transcribe audio using Whisper via Groq. Rotates keys on failure."""
    tried: set[str] = set()
    last_err = None

    for _attempt in range(key_manager.MAX_RETRIES):
        if not tried and override_key:
            key = override_key
        else:
            key = key_manager.get_next_key(exclude_keys=tried)
            if not key: key = key_manager.get_key()

        if not key or (key in tried and len(tried) >= key_manager.total_keys()):
            break
        tried.add(key)

        client = Groq(api_key=key)
        try:
            result = client.audio.transcriptions.create(
                file=("audio.wav", audio_bytes),
                model="whisper-large-v3",
                response_format="text",
            )
            key_manager.mark_used(key, token_count=200, model="whisper-large-v3")
            return result

        except Exception as e:
            err_str = str(e)
            last_err = e
            etype = _classify_error(err_str)

            if etype == "rate_limit":
                key_manager.mark_rate_limited(key, retry_after=_parse_retry_after(err_str))
                continue
            elif etype == "auth":
                key_manager.mark_invalid(key); continue
            else:
                key_manager.mark_error(key); continue

    raise ValueError(f"Audio transcription failed after {len(tried)} keys: {last_err}")
