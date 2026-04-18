"""
ai_engine.py — High-Level AI Orchestration v4.0
=================================================
v4.0: Single user-supplied API key — auto-detects provider (Gemini / Groq / Cerebras).
      9-key rotation system retired (all calls went through OmniKeyEngine).
      Groq and Cerebras now fully supported via their respective REST APIs.

Changes from v3:
  - generate() auto-routes to Gemini, Groq, or Cerebras based on key prefix
  - OmniKeyEngine is used ONLY for Gemini keys (single-key mode, v6)
  - Groq: uses /openai/v1/chat/completions with gsk_ key
  - Cerebras: uses /v1/chat/completions with csk- key
  - All other public API surface (generate_stream, json_generate, etc.) unchanged
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import re
import ssl
import sys
import time
import threading
import urllib.error
import urllib.request
from typing import Dict, Iterator, List, Optional

from utils.omnikey_engine import OMNI_ENGINE
from utils.prompts import get_engine_config

# -- Model defaults per provider --
GEMINI_MODELS: List[str] = ["gemini-2.5-flash"]
GROQ_MODEL    = "llama-3.1-8b-instant"       # fast free-tier model on Groq
CEREBRAS_MODEL = "llama3.1-8b"               # Cerebras Llama 3.1 8B

# -- In-memory response cache --
_mem_cache: Dict[str, str] = {}
_cache_lock = threading.Lock()
_CACHE_MAX = 300


def _cache_key(prompt: str, system: str) -> str:
    return hashlib.md5(f"{prompt}::{system}".encode()).hexdigest()


def _cache_get(k: str) -> Optional[str]:
    with _cache_lock:
        return _mem_cache.get(k)


def _cache_set(k: str, v: str) -> None:
    with _cache_lock:
        if len(_mem_cache) >= _CACHE_MAX:
            for old_k in list(_mem_cache.keys())[:50]:
                _mem_cache.pop(old_k, None)
        _mem_cache[k] = v


# -- Prompt helpers --
def _build_prompt(messages: list, context_text: str, prompt: str) -> str:
    turns: List[str] = []
    if context_text:
        turns.append(f"Context:\n{context_text}")
    for m in messages:
        role    = m.get("role", "user")
        content = m.get("content", "")
        turns.append(f"{role.capitalize()}: {content}")
    return "\n".join(turns)


def _apply_engine_config(
    engine_name: str, system: str, temperature: float, max_tokens: int, kwargs: dict
) -> tuple:
    cfg = get_engine_config(engine_name)
    out_system = (system + "\n\n" if system else "") + cfg["system"]
    out_temp   = kwargs.get("temperature", cfg["temperature"])
    out_tokens = kwargs.get("max_tokens",  cfg["max_tokens"])
    return out_system, out_temp, out_tokens


# -- Provider routing --
def _get_provider_and_key():
    """Return (key, provider) from user_key_store, or raise."""
    try:
        from utils.user_key_store import get_user_key
        key, provider = get_user_key()
        if key and provider:
            return key, provider
    except Exception:
        pass
    raise RuntimeError(
        "No API key set. Please enter your API key (Gemini / Groq / Cerebras) "
        "in the sidebar to continue."
    )


def _make_ssl():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        try:
            return ssl.create_default_context()
        except Exception:
            return None
    except Exception:
        return None


_ssl_ctx = None
_ssl_lock = threading.Lock()

def _ssl():
    global _ssl_ctx
    with _ssl_lock:
        if _ssl_ctx is None:
            _ssl_ctx = _make_ssl()
    return _ssl_ctx


def _call_groq(
    key: str,
    prompt: str,
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    model: str = GROQ_MODEL,
) -> str:
    """Call Groq OpenAI-compatible endpoint."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode()

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90, context=_ssl()) as resp:
            raw = json.loads(resp.read())
            usage = raw.get("usage", {}).get("total_tokens", 0)
            return raw["choices"][0]["message"]["content"], usage
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode(errors="replace")
        except Exception:
            pass
        raise RuntimeError(f"Groq HTTP {e.code}: {body_text}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Groq network error: {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Groq unexpected: {e}")


def _call_cerebras(
    key: str,
    prompt: str,
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    model: str = CEREBRAS_MODEL,
) -> str:
    """Call Cerebras OpenAI-compatible endpoint."""
    url = "https://api.cerebras.ai/v1/chat/completions"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode()

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90, context=_ssl()) as resp:
            raw = json.loads(resp.read())
            usage = raw.get("usage", {}).get("total_tokens", 0)
            return raw["choices"][0]["message"]["content"], usage
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode(errors="replace")
        except Exception:
            pass
        raise RuntimeError(f"Cerebras HTTP {e.code}: {body_text}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cerebras network error: {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Cerebras unexpected: {e}")


# -- Core generate() --
def generate(
    prompt: str = "",
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    image_data: str = "",
    image_mime: str = "image/jpeg",
    messages: list = None,
    context_text: str = "",
    model: str = "",
    **kwargs,
) -> str:
    """
    Generate a response using whichever provider key the user has entered.
    Automatically routes to Gemini, Groq, or Cerebras.
    """
    if messages:
        prompt = _build_prompt(messages, context_text, prompt)

    engine_name = kwargs.get("engine_name")
    if engine_name:
        system, temperature, max_tokens = _apply_engine_config(
            engine_name, system, temperature, max_tokens, kwargs
        )

    persona_prompt = kwargs.get("persona_prompt", "")
    if persona_prompt:
        system = (system + "\n\n" if system else "") + persona_prompt

    from utils.emoji_bank import EMOJI_BANK
    from utils.emoji_intelligence import EMOJI_INTELLIGENCE_PROMPT
    system = (system + "\n\n" if system else "") + (
        f"── UNIVERSAL EMOJI OVERRIDE (AESTHETIC PROTOCOL) ──\n"
        f"You have access to a massive sensory emoji bank containing over 1,000+ emojis.\n"
        f"ルール (RULES FOR EMOJI USE):\n"
        f"1. AESTHETIC SPACING: Do NOT spam emojis randomly mid-sentence. That looks cheap.\n"
        f"2. PURPOSEFUL PLACEMENT: Use emojis at the end of paragraphs as emotional punctuation, or at the start of bullet points/lists to create beautiful formatting.\n"
        f"3. SENSORY MATCHING: Cross-reference your current topic (medical, coding, thriller story) and select the EXACT specialized emoji from the bank that matches the subtext.\n"
        f"4. DOSAGE: Use 1-3 emojis per output block for maximum impact. Less is more, but aim for high-relevance.\n\n"
        f"EMOJI BANK:\n{EMOJI_BANK}\n\n"
        f"{EMOJI_INTELLIGENCE_PROMPT}"
    )

    # Cache check (skip for vision)
    if not image_data:
        ck = _cache_key(prompt, system)
        cached = _cache_get(ck)
        if cached:
            return cached

    from utils.token_tracker import track_tokens, check_limit_stop
    if check_limit_stop():
        raise RuntimeError("🛑 API Limit Reached: Generation is strictly blocked by the Telemetry Engine.")

    result: Optional[str] = None
    exact_toks: Optional[int] = None

    if provider == "gemini":
        for model_name in GEMINI_MODELS:
            try:
                result, exact_toks = OMNI_ENGINE.execute(
                    model=model_name,
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    image_b64=image_data,
                    image_mime=image_mime,
                )
                if result:
                    break
            except Exception as e:
                err_str = str(e)
                if any(kw in err_str for kw in ("rate limit", "wait", "invalid", "revoked")):
                    raise
                print(f"[ai_engine] Gemini model {model_name} failed: {err_str[:80]}", file=sys.stderr)

    elif provider == "groq":
        result, exact_toks = _call_groq(
            key=key,
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model or GROQ_MODEL,
        )

    elif provider == "cerebras":
        c_model = model or CEREBRAS_MODEL
        if c_model and "70b" in c_model.lower():
            c_model = "llama3.3-70b"
        elif c_model and "8b" in c_model.lower():
            c_model = "llama3.1-8b"
            
        result, exact_toks = _call_cerebras(
            key=key,
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            model=c_model,
        )

    else:
        raise RuntimeError(f"Unknown provider: {provider}")

    if not result:
        raise RuntimeError("No response received from the AI provider.")

    if not image_data:
        _cache_set(_cache_key(prompt, system), result)

    track_tokens(provider, result, exact_tokens=exact_toks)

    return result


# -- Streaming generate --
def generate_stream(
    prompt: str = "",
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    image_data: str = "",
    image_mime: str = "image/jpeg",
    messages: list = None,
    context_text: str = "",
    chunk_words: int = 6,
    **kwargs,
) -> Iterator[str]:
    """
    Yields word-chunks for smooth Streamlit streaming.
    Falls back to chunking the full generate() response for non-Gemini providers.
    """
    if messages:
        prompt = _build_prompt(messages, context_text, prompt)

    engine_name = kwargs.get("engine_name")
    if engine_name:
        system, temperature, max_tokens = _apply_engine_config(
            engine_name, system, temperature, max_tokens, kwargs
        )

    persona_prompt = kwargs.get("persona_prompt", "")
    if persona_prompt:
        system = (system + "\n\n" if system else "") + persona_prompt

    from utils.emoji_bank import EMOJI_BANK
    from utils.emoji_intelligence import EMOJI_INTELLIGENCE_PROMPT
    system = (system + "\n\n" if system else "") + (
        f"── UNIVERSAL EMOJI OVERRIDE (AESTHETIC PROTOCOL) ──\n"
        f"You have access to a massive sensory emoji bank containing over 1,000+ emojis.\n"
        f"ルール (RULES FOR EMOJI USE):\n"
        f"1. AESTHETIC SPACING: Do NOT spam emojis randomly mid-sentence. That looks cheap.\n"
        f"2. PURPOSEFUL PLACEMENT: Use emojis at the end of paragraphs as emotional punctuation, or at the start of bullet points/lists to create beautiful formatting.\n"
        f"3. SENSORY MATCHING: Cross-reference your current topic (medical, coding, thriller story) and select the EXACT specialized emoji from the bank that matches the subtext.\n"
        f"4. DOSAGE: Use 1-3 emojis per output block for maximum impact. Less is more, but aim for high-relevance.\n\n"
        f"EMOJI BANK:\n{EMOJI_BANK}\n\n"
        f"{EMOJI_INTELLIGENCE_PROMPT}"
    )

    from utils.token_tracker import track_tokens, check_limit_stop
    if check_limit_stop():
        return

    key, provider = _get_provider_and_key()

    if provider == "gemini":
        for model_name in GEMINI_MODELS:
            try:
                # Wrap the generator for live telemetry tracking per chunk
                for chunk in OMNI_ENGINE.execute_stream(
                    model=model_name,
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    image_b64=image_data,
                    image_mime=image_mime,
                    chunk_words=chunk_words,
                ):
                    track_tokens(provider, chunk)
                    yield chunk
                return
            except Exception as e:
                err_str = str(e)
                if any(kw in err_str for kw in ("rate limit", "wait", "invalid", "revoked")):
                    raise
                print(f"[ai_engine] Stream Gemini {model_name} failed: {err_str[:80]}", file=sys.stderr)
    else:
        # Groq and Cerebras: call full generate and chunk manually
        full = generate(
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        words = full.split(" ")
        chunk: List[str] = []
        for i, word in enumerate(words):
            chunk.append(word)
            if len(chunk) >= chunk_words or i == len(words) - 1:
                yield " ".join(chunk) + (" " if i < len(words) - 1 else "")
                chunk = []


# -- Convenience wrappers --
def quick_generate(prompt: str, system: str = "", **kwargs) -> str:
    return generate(prompt=prompt, system=system, max_tokens=2048, **kwargs)


def vision_generate(prompt: str, image_b64: str, mime: str = "image/jpeg", **kwargs) -> str:
    return generate(prompt=prompt, image_data=image_b64, image_mime=mime, **kwargs)


def json_generate(prompt: str, system: str = "", **kwargs) -> str:
    import re as _re
    kwargs.pop("json_mode", None)

    def _extract_and_validate(raw: str) -> Optional[str]:
        fence_match = _re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        if fence_match:
            candidate = fence_match.group(1).strip()
        else:
            candidate = None
            for start_char in ("{", "["):
                idx = raw.find(start_char)
                if idx != -1:
                    candidate = raw[idx:].rstrip()
                    break
        if candidate is None:
            return None
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            return None

    json_system = (
        (system + "\n\n" if system else "") +
        "IMPORTANT: Respond with ONLY valid JSON. No markdown, no preamble, no explanation."
    )
    raw = generate(prompt=prompt, system=json_system, temperature=0.2, **kwargs)
    result = _extract_and_validate(raw)
    if result:
        return result

    strict_system = "Return ONLY a raw JSON object. No text before or after it. No markdown. No code fences."
    try:
        raw2 = generate(prompt=prompt, system=strict_system, temperature=0.1, **kwargs)
        result2 = _extract_and_validate(raw2)
        if result2:
            return result2
    except Exception:
        pass

    return raw


def generate_with_retry(prompt: str, max_retries: int = 3, **kwargs) -> str:
    delay = 1.0
    last_err: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            return generate(prompt=prompt, **kwargs)
        except RuntimeError as e:
            err_str = str(e)
            if any(kw in err_str for kw in ("rate limit", "wait", "invalid", "revoked")):
                raise
            last_err = e
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2
    raise last_err or RuntimeError("generate_with_retry: all retries exhausted.")


def batch_generate(prompts: List[str], **kwargs) -> List[str]:
    results: List[str] = [""] * len(prompts)

    def _task(idx: int, p: str) -> None:
        try:
            results[idx] = generate(prompt=p, **kwargs)
        except Exception as e:
            results[idx] = f"[Error: {str(e)[:100]}]"

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(_task, i, p) for i, p in enumerate(prompts)]
        concurrent.futures.wait(futures)

    return results


# -- Status & Admin --
def get_pool_status() -> dict:
    return OMNI_ENGINE.get_status_report()


def get_capacity_summary() -> str:
    return OMNI_ENGINE.get_key_status_line()


def get_dashboard_html() -> str:
    return OMNI_ENGINE.get_dashboard_html()


def reset_all_keys() -> None:
    OMNI_ENGINE.reset_all_cooldowns()


def get_token_usage_summary() -> dict:
    total_in  = sum(s.total_tokens_in  for s in OMNI_ENGINE.slots)
    total_out = sum(s.total_tokens_out for s in OMNI_ENGINE.slots)
    cost = (total_in / 1_000_000 * 0.075) + (total_out / 1_000_000 * 0.30)
    return {
        "total_in":           total_in,
        "total_out":          total_out,
        "estimated_cost_usd": round(cost, 6),
    }


# -- Backward-compat stubs --
def stream_chat_with_groq(*args, **kwargs) -> Iterator[str]:
    return generate_stream(**kwargs)


def chat_with_groq(*args, **kwargs) -> str:
    return generate(**kwargs)
