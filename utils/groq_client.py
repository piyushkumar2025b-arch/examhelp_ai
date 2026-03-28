"""
groq_client.py — Groq API client with full automatic key rotation.

Every call (streaming or not) automatically:
  1. Picks the key with the most headroom (fewest tokens used this minute).
  2. On rate-limit (429) → immediately marks that key, picks next key, retries.
  3. Retries across ALL available keys before giving up.
  4. Reports token usage back to key_manager after every successful call
     so the rolling-window limiter stays accurate.
"""

from __future__ import annotations
import time
import re
import requests
from typing import Generator, Optional

from groq import Groq
from utils import key_manager

# ── Models ────────────────────────────────────────────────────────────────────
MODEL          = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"
MAX_CONTEXT_CHARS = 25_000

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are ExamHelp AI, a GOD-LEVEL Study Architect and Academic Reasoning Engine.

TRANSFORMATION PROTOCOL — DEEP-THINK MODE:
1. AXIOMATIC EXPLANATION: Start every complex topic from first principles.
2. LONG-FORM SCHOLARSHIP: For academic queries provide 4-8 comprehensive paragraphs.
3. VISUAL MANIFEST (MANDATORY): If a concept is spatial/physical/geometric, append at the end:
   ---
   VISUAL_MANIFEST: {"query": "specific image search terms", "caption": "technical description"}
   ---
4. SOURCE-SYNC: If [STUDY MATERIAL] context is provided, explicitly reference it.

RESPONSE ARCHITECTURE:
## 🧠 Conceptual Axioms
## 🔍 Logic & Deep-Dive
## 🛠️ Procedural Steps
## 🧪 Real-World Proof
## 🎯 Exam Strategy

TONE: Intellectually elite, authoritative, exhaustive.\
"""


# ── Wikipedia quick-context helper ───────────────────────────────────────────

def _fetch_wiki_context(query: str) -> str:
    try:
        clean_q = re.sub(
            r'\b(what|is|the|explain|how|why|who|a|an|describe|tell|me|about|calculate)\b',
            '', query, flags=re.IGNORECASE
        ).strip()
        if len(clean_q) < 3:
            return ""
        term = " ".join(clean_q.split()[:3])
        resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action": "query", "format": "json", "prop": "extracts",
                    "exsentences": "4", "exlimit": "1", "titles": term,
                    "explaintext": "1", "formatversion": "2", "redirects": "1"},
            timeout=1.5
        )
        if resp.status_code == 200:
            pages = resp.json().get("query", {}).get("pages", [])
            if pages and pages[0].get("extract", "").strip():
                return pages[0]["extract"].strip()
    except Exception:
        pass
    return ""


# ── Message builder ───────────────────────────────────────────────────────────

def _build_messages(history: list[dict], context_text: str) -> list[dict]:
    messages: list[dict] = []

    if context_text:
        trimmed = context_text[:MAX_CONTEXT_CHARS]
        hint = ""
        if "[Page " in trimmed:
            hint = " (PDF)"
        elif "YouTube Video Transcript" in trimmed:
            hint = " (YouTube transcript)"
        elif "Web Article:" in trimmed:
            hint = " (web article)"
        messages.append({"role": "user", "content":
            f"=== STUDY MATERIAL{hint} ===\n\n{trimmed}\n\n=== END ===\n\n"
            "Please acknowledge you have received this study material."})
        messages.append({"role": "assistant", "content":
            "✅ Study material received. Ready to provide precise, source-grounded answers."})

    # Inject quick Wikipedia context for the latest user query
    last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), None)
    if last_user:
        wiki_ctx = _fetch_wiki_context(last_user)
        if wiki_ctx:
            messages.append({"role": "system", "content":
                f"[SYSTEM: Background fact retrieved — integrate into answer: {wiki_ctx}]"})

    messages.extend(history)
    return messages


# ── Core helper: execute one attempt ─────────────────────────────────────────

def _try_call(client: Groq, model: str, sys_prompt: str,
              messages: list[dict], json_mode: bool,
              stream: bool, max_tokens: int, temperature: float):
    """Single non-retrying API call. Returns (result, usage_tokens)."""
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
        return completion, 0   # tokens counted after stream exhausted
    else:
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
    Yield response text chunks. Automatically rotates keys on rate-limit.
    Tries every available key before giving up.
    """
    messages   = _build_messages(history, context_text)
    sys_prompt = SYSTEM_PROMPT + ("\n\n" + persona_prompt if persona_prompt else "")
    chosen_model = model or MODEL
    tried: set[str] = set()
    last_err = None

    for attempt in range(key_manager.MAX_RETRIES):
        key = (override_key if attempt == 0 else None) or key_manager.get_next_key(
            exclude_key=next(iter(tried), None)
        ) or key_manager.get_key()

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
                max_tokens=4096, temperature=0.65
            )
            total_tokens = 0
            for chunk in stream_obj:
                delta = chunk.choices[0].delta.content
                if delta:
                    total_tokens += len(delta.split())   # rough estimate
                    yield delta

            key_manager.mark_used(key, token_count=total_tokens * 4 // 3)  # words→tokens approx
            return

        except Exception as e:
            err = str(e).lower()
            last_err = e

            if "rate_limit" in err or "429" in err:
                key_manager.mark_rate_limited(key)
                time.sleep(0.5)    # tiny pause before switching
                continue           # next key

            if "model_not_found" in err or ("model" in err and "not" in err):
                # Try fallback model on same key before moving on
                try:
                    stream_obj2, _ = _try_call(
                        client, FALLBACK_MODEL, sys_prompt, messages,
                        json_mode=False, stream=True,
                        max_tokens=4096, temperature=0.65
                    )
                    total_tokens = 0
                    for chunk in stream_obj2:
                        delta = chunk.choices[0].delta.content
                        if delta:
                            total_tokens += len(delta.split())
                            yield delta
                    key_manager.mark_used(key, token_count=total_tokens * 4 // 3)
                    return
                except Exception:
                    pass
                continue

            if "authentication" in err or "api_key" in err or "401" in err or "invalid" in err:
                key_manager.mark_invalid(key)
                continue

            # Unknown error — try next key
            continue

    if last_err:
        raise last_err
    raise ValueError("All Groq API keys exhausted or unavailable.")


# ── Public: non-streaming (JSON / tool calls) ─────────────────────────────────

def chat_with_groq(
    messages: list[dict],
    json_mode: bool = False,
    override_key: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    Non-streaming call. Automatically retries with next key on rate-limit.
    Returns the response text (or JSON string).
    """
    chosen_model = model or MODEL
    tried: set[str] = set()
    last_err = None

    for attempt in range(key_manager.MAX_RETRIES):
        key = (override_key if attempt == 0 else None) or key_manager.get_next_key(
            exclude_key=next(iter(tried), None)
        ) or key_manager.get_key()

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
                max_tokens=2048, temperature=0.3 if json_mode else 0.7
            )
            key_manager.mark_used(key, token_count=tokens)
            return text

        except Exception as e:
            err = str(e).lower()
            last_err = e

            if "rate_limit" in err or "429" in err:
                key_manager.mark_rate_limited(key)
                time.sleep(0.3)
                continue

            if "model_not_found" in err or ("model" in err and "not" in err):
                try:
                    text, tokens = _try_call(
                        client, FALLBACK_MODEL, SYSTEM_PROMPT, messages,
                        json_mode=json_mode, stream=False,
                        max_tokens=2048, temperature=0.3 if json_mode else 0.7
                    )
                    key_manager.mark_used(key, token_count=tokens)
                    return text
                except Exception as e2:
                    last_err = e2
                    continue

            if "authentication" in err or "api_key" in err or "401" in err or "invalid" in err:
                key_manager.mark_invalid(key)
                continue

            continue

    if last_err:
        raise last_err
    raise ValueError("All Groq API keys exhausted or unavailable.")


# ── Audio transcription ───────────────────────────────────────────────────────

def transcribe_audio(audio_bytes: bytes, override_key: Optional[str] = None) -> str:
    """Groq Whisper transcription with key rotation on rate-limit."""
    tried: set[str] = set()
    last_err = None

    for attempt in range(key_manager.MAX_RETRIES):
        key = (override_key if attempt == 0 else None) or key_manager.get_next_key(
            exclude_key=next(iter(tried), None)
        ) or key_manager.get_key()

        if not key or (key in tried and len(tried) >= key_manager.total_keys()):
            break
        tried.add(key)

        client = Groq(api_key=key)
        try:
            result = client.audio.transcriptions.create(
                file=("audio.wav", audio_bytes),
                model="whisper-large-v3",
                response_format="text"
            )
            key_manager.mark_used(key, token_count=200)   # audio tokens are cheaper
            return result
        except Exception as e:
            err = str(e).lower()
            last_err = e
            if "rate_limit" in err or "429" in err:
                key_manager.mark_rate_limited(key)
                time.sleep(0.3)
                continue
            if "authentication" in err or "api_key" in err or "401" in err or "invalid" in err:
                key_manager.mark_invalid(key)
                continue
            continue

    raise ValueError(f"Audio transcription failed: {last_err}")
