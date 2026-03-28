"""
groq_client.py — Uncrashable Groq client with 4-dimension rate tracking.

ARCHITECTURE
============

  REQUEST FLOW (per call):
  ┌─────────────────────────────────────────────────────────┐
  │  1. key_manager picks key with MOST headroom            │
  │     (considers RPM + TPM + RPD + TPD simultaneously)   │
  │  2. Call executes                                       │
  │  3. Response headers parsed → live remaining fed back  │
  │     into key_manager (x-ratelimit-remaining-tokens etc)│
  │  4. If 429 → parse retry-after → hard cooldown         │
  │     → instantly try next best key (no sleep needed)    │
  │  5. Exhausted all keys? → raise → Gemini fallback      │
  │     in app.py catches and continues transparently      │
  └─────────────────────────────────────────────────────────┘

  GROQ FREE TIER (12 keys x limits):
    llama-3.3-70b-versatile: 30 RPM | 12K TPM | 1K RPD | 100K TPD
    llama-3.1-8b-instant:    30 RPM |  6K TPM | 14.4K RPD | 500K TPD
    Combined theoretical max (12 keys): 360 RPM | 144K TPM/min
"""

from __future__ import annotations
import time
import re
import requests as _requests
from typing import Generator, Optional

from groq import Groq
from utils import key_manager

MODEL          = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"
MAX_CONTEXT_CHARS = 25_000

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


# ── Wikipedia quick-context ───────────────────────────────────────────────────

def _fetch_wiki_context(query: str) -> str:
    try:
        clean_q = re.sub(
            r'\b(what|is|the|explain|how|why|who|a|an|describe|tell|me|about|calculate)\b',
            '', query, flags=re.IGNORECASE
        ).strip()
        if len(clean_q) < 3: return ""
        term = " ".join(clean_q.split()[:3])
        resp = _requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={"action":"query","format":"json","prop":"extracts",
                    "exsentences":"4","exlimit":"1","titles":term,
                    "explaintext":"1","formatversion":"2","redirects":"1"},
            timeout=1.5
        )
        if resp.status_code == 200:
            pages = resp.json().get("query",{}).get("pages",[])
            if pages and pages[0].get("extract","").strip():
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
        if "[Page " in trimmed: hint = " (PDF)"
        elif "YouTube Video Transcript" in trimmed: hint = " (YouTube transcript)"
        elif "Web Article:" in trimmed: hint = " (web article)"
        messages.append({"role":"user","content":
            f"=== STUDY MATERIAL{hint} ===\n\n{trimmed}\n\n=== END ===\n\n"
            "Please acknowledge you have received this study material."})
        messages.append({"role":"assistant","content":
            "✅ Study material received. Ready to provide precise, source-grounded answers."})
    last_user = next((m["content"] for m in reversed(history) if m["role"]=="user"), None)
    if last_user:
        wiki_ctx = _fetch_wiki_context(last_user)
        if wiki_ctx:
            messages.append({"role":"system","content":
                f"[SYSTEM: Background fact: {wiki_ctx}]"})
    messages.extend(history)
    return messages


# ── Parse retry-after from 429 error ─────────────────────────────────────────

def _parse_retry_after(err_str: str) -> Optional[float]:
    """Extract retry wait seconds from Groq 429 error message."""
    m = re.search(r'try again in ([0-9.]+)s', err_str, re.IGNORECASE)
    if m: return float(m.group(1))
    m = re.search(r'retry.after["\s:]+([0-9.]+)', err_str, re.IGNORECASE)
    if m: return float(m.group(1))
    return None


def _extract_headers(exc) -> dict:
    """Try to pull rate-limit headers from a Groq SDK exception."""
    try:
        resp = getattr(exc, 'response', None)
        if resp is not None and hasattr(resp, 'headers'):
            return dict(resp.headers)
    except Exception:
        pass
    return {}


# ── Core single-attempt call ──────────────────────────────────────────────────

def _try_call(client: Groq, model: str, sys_prompt: str,
              messages: list[dict], json_mode: bool,
              stream: bool, max_tokens: int, temperature: float):
    fmt = {"type":"json_object"} if json_mode else {"type":"text"}
    kwargs = dict(
        model=model,
        messages=[{"role":"system","content":sys_prompt}] + messages,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=0.9,
    )
    if not stream:
        kwargs["response_format"] = fmt
    completion = client.chat.completions.create(stream=stream, **kwargs)
    if stream:
        return completion, 0
    tokens = 0
    try: tokens = completion.usage.total_tokens or 0
    except Exception: pass
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
    Stream response. Rotates keys proactively — no 429 should ever reach the user.
    Exhausts all 12 Groq keys before raising (Gemini fallback catches in app.py).
    """
    messages     = _build_messages(history, context_text)
    sys_prompt   = SYSTEM_PROMPT + ("\n\n" + persona_prompt if persona_prompt else "")
    chosen_model = model or MODEL
    tried: set[str] = set()
    last_err = None

    for _attempt in range(key_manager.MAX_RETRIES):
        # Pick best key not yet tried
        if not tried and override_key:
            key = override_key
        else:
            key = key_manager.get_next_key(exclude_keys=tried) or key_manager.get_key()

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
            response_headers = {}

            for chunk in stream_obj:
                # Try to read headers from the underlying response
                try:
                    if not response_headers and hasattr(chunk, '_raw_response'):
                        response_headers = dict(chunk._raw_response.headers)
                except Exception:
                    pass

                delta = chunk.choices[0].delta.content
                if delta:
                    total_tokens += len(delta.split())
                    yield delta

            # Approximate words -> tokens (1 word ≈ 1.33 tokens)
            key_manager.mark_used(key, token_count=int(total_tokens * 1.33),
                                  headers=response_headers or None)
            return

        except Exception as e:
            err = str(e).lower()
            last_err = e
            headers = _extract_headers(e)

            if "rate_limit" in err or "429" in err:
                retry_after = _parse_retry_after(str(e))
                key_manager.mark_rate_limited(key, retry_after=retry_after)
                # NO sleep — instantly switch to next key
                continue

            if "model_not_found" in err or ("model" in err and "not" in err):
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
                    key_manager.mark_used(key, token_count=int(total_tokens * 1.33))
                    return
                except Exception:
                    pass
                continue

            if "authentication" in err or "api_key" in err or "401" in err or "invalid" in err:
                key_manager.mark_invalid(key)
                continue

            # Unknown error — next key
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
    chosen_model = model or MODEL
    tried: set[str] = set()
    last_err = None

    for _attempt in range(key_manager.MAX_RETRIES):
        if not tried and override_key:
            key = override_key
        else:
            key = key_manager.get_next_key(exclude_keys=tried) or key_manager.get_key()

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
                retry_after = _parse_retry_after(str(e))
                key_manager.mark_rate_limited(key, retry_after=retry_after)
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

    if last_err: raise last_err
    raise ValueError("All Groq API keys exhausted.")


# ── Audio transcription ───────────────────────────────────────────────────────

def transcribe_audio(audio_bytes: bytes, override_key: Optional[str] = None) -> str:
    tried: set[str] = set()
    last_err = None
    for _attempt in range(key_manager.MAX_RETRIES):
        if not tried and override_key:
            key = override_key
        else:
            key = key_manager.get_next_key(exclude_keys=tried) or key_manager.get_key()
        if not key or (key in tried and len(tried) >= key_manager.total_keys()): break
        tried.add(key)
        client = Groq(api_key=key)
        try:
            result = client.audio.transcriptions.create(
                file=("audio.wav", audio_bytes),
                model="whisper-large-v3",
                response_format="text"
            )
            key_manager.mark_used(key, token_count=200)
            return result
        except Exception as e:
            err = str(e).lower()
            last_err = e
            if "rate_limit" in err or "429" in err:
                key_manager.mark_rate_limited(key, retry_after=_parse_retry_after(str(e)))
                continue
            if "authentication" in err or "401" in err or "invalid" in err:
                key_manager.mark_invalid(key)
                continue
            continue
    raise ValueError(f"Audio transcription failed: {last_err}")
