"""
ai_engine.py — High-Level AI Orchestration v3.0
=================================================
Delegates all Gemini operations to the EliteKey OmniKeyEngine.
Maintains full backward compatibility with existing app.py callers.

Changes v3.0:
  - True streaming (word-chunk yields from OmniKeyEngine.execute_stream)
  - Model cascade: tries each model in order, switches seamlessly
  - generate() never blocks the UI — all waits happen inside OmniKeyEngine
  - get_capacity_summary() returns real per-key RPM/cooldown data
  - reset_all_keys() delegates to engine.reset_all_cooldowns()
"""

from __future__ import annotations

import hashlib
import re
import sys
import time
import threading
from typing import Dict, Iterator, List, Optional

from utils.omnikey_engine import OMNI_ENGINE
from utils.prompts import get_engine_config

# ── Model Priority (confirmed-working first) ──────────────────────────────────
GEMINI_MODELS: List[str] = [
    "gemini-2.5-flash",           # As requested, only use 2.5 flash
]

# ── In-memory response cache (prevents re-querying identical prompts) ─────────
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
            # Evict oldest 50
            for old_k in list(_mem_cache.keys())[:50]:
                _mem_cache.pop(old_k, None)
        _mem_cache[k] = v


# ── Prompt helpers ────────────────────────────────────────────────────────────
def _build_prompt(messages: list, context_text: str, prompt: str) -> str:
    """Convert messages list + context into a single flat prompt string."""
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
    """Inject engine-specific system prompt / temperature / tokens."""
    cfg = get_engine_config(engine_name)
    out_system = (system + "\n\n" if system else "") + cfg["system"]
    out_temp   = kwargs.get("temperature", cfg["temperature"])
    out_tokens = kwargs.get("max_tokens",  cfg["max_tokens"])
    return out_system, out_temp, out_tokens


# ── Core generate() ───────────────────────────────────────────────────────────
def generate(
    prompt: str = "",
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    image_data: str = "",
    image_mime: str = "image/jpeg",
    messages: list = None,
    context_text: str = "",
    model: str = "",          # optional model override (ignored — engine picks best)
    **kwargs,
) -> str:
    """
    Generate a response using the OmniKeyEngine rotation system.
    Thread-safe, cached, and model-cascade-aware.
    Any 429/rate-limit errors are handled transparently by the engine.
    """
    if messages:
        prompt = _build_prompt(messages, context_text, prompt)

    engine_name = kwargs.get("engine_name")
    if engine_name:
        system, temperature, max_tokens = _apply_engine_config(
            engine_name, system, temperature, max_tokens, kwargs
        )

    # Persona/language injections
    persona_prompt = kwargs.get("persona_prompt", "")
    if persona_prompt:
        system = (system + "\n\n" if system else "") + persona_prompt

    # Cache check (skip for vision requests)
    if not image_data:
        ck = _cache_key(prompt, system)
        cached = _cache_get(ck)
        if cached:
            return cached

    # Try each model in cascade order
    last_err: Optional[Exception] = None
    for model_name in GEMINI_MODELS:
        try:
            result = OMNI_ENGINE.execute(
                model=model_name,
                prompt=prompt,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens,
                image_b64=image_data,
                image_mime=image_mime,
            )
            if result:
                if not image_data:
                    _cache_set(_cache_key(prompt, system), result)
                return result
        except Exception as e:
            last_err = e
            err_str = str(e)
            # If ALL keys are exhausted (engine gave up), re-raise immediately
            # rather than trying the same exhausted pool with another model
            if "exhausted" in err_str or "To make it work" in err_str:
                import streamlit as st
                st.error(f"🚨 **Free Tier Exhaustion**\n\n{err_str}")
                st.stop()
            print(
                f"[ai_engine] Model {model_name} failed: {err_str[:80]}. Trying next...",
                file=sys.stderr
            )
            continue

    raise last_err or RuntimeError(
        "No Gemini response possible — all models and keys exhausted."
    )


# ── Streaming generate ────────────────────────────────────────────────────────
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
    Internally calls generate() with full model cascade and key rotation.
    The user always sees output — no blank wait screen.
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

    last_err: Optional[Exception] = None
    for model_name in GEMINI_MODELS:
        try:
            yield from OMNI_ENGINE.execute_stream(
                model=model_name,
                prompt=prompt,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens,
                image_b64=image_data,
                image_mime=image_mime,
                chunk_words=chunk_words,
            )
            return  # success — stop cascade
        except Exception as e:
            last_err = e
            err_str = str(e)
            if "exhausted" in err_str or "To make it work" in err_str:
                import streamlit as st
                st.error(f"🚨 **Free Tier Exhaustion**\n\n{err_str}")
                st.stop()
            print(
                f"[ai_engine] Stream model {model_name} failed: {err_str[:80]}. Trying next...",
                file=sys.stderr
            )
            continue

    raise last_err or RuntimeError(
        "No Gemini stream possible — all models and keys exhausted."
    )


# ── Convenience wrappers (backward compat) ────────────────────────────────────
def quick_generate(prompt: str, system: str = "", **kwargs) -> str:
    return generate(prompt=prompt, system=system, max_tokens=2048, **kwargs)


def vision_generate(prompt: str, image_b64: str, mime: str = "image/jpeg", **kwargs) -> str:
    return generate(prompt=prompt, image_data=image_b64, image_mime=mime, **kwargs)


def json_generate(prompt: str, system: str = "", **kwargs) -> str:
    """
    Generate a response and extract the first JSON object/array from it.
    Also handles callers that pass json_mode=True kwarg (silently consumed).
    Falls back to raw text if no JSON block is found.
    """
    import re as _re
    kwargs.pop("json_mode", None)  # consume silently — we handle JSON ourselves
    # Inject JSON instruction into system prompt
    json_system = (
        (system + "\n\n" if system else "") +
        "IMPORTANT: Respond with ONLY valid JSON. No markdown, no preamble, no explanation."
    )
    raw = generate(prompt=prompt, system=json_system, temperature=0.2, **kwargs)
    # Try to extract JSON from code fences or raw text
    fence_match = _re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
    if fence_match:
        return fence_match.group(1).strip()
    # Find first { or [ and pair it
    for start_char, end_char in (("{", "}"), ("[", "]")):
        idx = raw.find(start_char)
        if idx != -1:
            return raw[idx:].rstrip()
    return raw  # fallback — return raw if no JSON found


# ── Status & Admin ────────────────────────────────────────────────────────────
def get_pool_status() -> dict:
    """Return full real-time status report from OmniKeyEngine."""
    return OMNI_ENGINE.get_status_report()


def get_capacity_summary() -> str:
    """Single-line summary string for display in sidebar/header."""
    return OMNI_ENGINE.get_key_status_line()


def get_dashboard_html() -> str:
    """Rich HTML dashboard for embedding in Streamlit with unsafe_allow_html."""
    return OMNI_ENGINE.get_dashboard_html()


def reset_all_keys() -> None:
    """Reset all key cooldowns (emergency override)."""
    OMNI_ENGINE.reset_all_cooldowns()


# ── Removed integration stubs (backward compat) ──────────────────────────────
def stream_chat_with_groq(*args, **kwargs) -> Iterator[str]:
    return generate_stream(**kwargs)


def chat_with_groq(*args, **kwargs) -> str:
    return generate(**kwargs)
