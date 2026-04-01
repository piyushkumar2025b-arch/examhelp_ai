"""
ai_engine.py — High-Level AI Orchestration
===========================================
Delegates all Gemini operations to the God-Tier OmniKeyEngine.
Maintains backward compatibility for the application's clean API.
"""

from __future__ import annotations
import hashlib
import re
import sys
import time
import threading
from typing import Iterator, Optional, Dict, List
from utils.omnikey_engine import OMNI_ENGINE
from utils.prompts import get_engine_config

# --- Model Selection (ordered: confirmed working first) ---
# gemini-2.5-flash-lite : CONFIRMED WORKING (tested live)
# gemini-2.5-flash      : 20 req/day free tier
# gemini-2.0-flash-001  : pinned stable version
# gemini-2.0-flash / flash-lite: last resort
GEMINI_MODELS = [
    "gemini-2.5-flash-lite",   # CONFIRMED WORKING — highest available quota
    "gemini-2.5-flash",        # 20 req/day
    "gemini-2.0-flash-001",    # pinned stable
    "gemini-2.0-flash",        # fallback
    "gemini-2.0-flash-lite",   # last resort
]

MODEL_RETRY_ROUNDS = 3   # Retry the full model cascade this many times
RETRY_WAIT_SEC = 25      # Wait between retry rounds

# --- Global Cache ---
_mem_cache: Dict[str, str] = {}
_cache_lock = threading.Lock()

def _get_cache_key(prompt: str, system: str, model: str) -> str:
    return hashlib.md5(f"{prompt}:{system}:{model}".encode()).hexdigest()

def _build_prompt(messages: list, context_text: str, prompt: str) -> str:
    """Convert a messages list into a single prompt string."""
    turns = []
    if context_text:
        turns.append(f"Context:\n{context_text}")
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        turns.append(f"{role.capitalize()}: {content}")
    return "\n".join(turns)


def _apply_engine_config(engine_name: str, system: str, temperature: float, max_tokens: int, kwargs: dict):
    """Inject engine-specific prompt/temperature/tokens from the prompts registry."""
    cfg = get_engine_config(engine_name)
    out_system = (system + "\n\n" if system else "") + cfg["system"]
    out_temp = kwargs.get("temperature", cfg["temperature"])
    out_tokens = kwargs.get("max_tokens", cfg["max_tokens"])
    return out_system, out_temp, out_tokens


def _cache_get(key: str) -> Optional[str]:
    with _cache_lock:
        return _mem_cache.get(key)


def _cache_set(key: str, value: str) -> None:
    with _cache_lock:
        if len(_mem_cache) > 500:
            _mem_cache.clear()
        _mem_cache[key] = value


def _compute_wait(last_err: Exception) -> float:
    """Get wait seconds from a 429 error, or fall back to RETRY_WAIT_SEC."""
    match = re.search(r'retry in (\d+\.?\d*)\s*s', str(last_err), re.IGNORECASE)
    if match:
        return max(float(match.group(1)) + 2, RETRY_WAIT_SEC)
    return RETRY_WAIT_SEC


def _try_model(model_name: str, prompt: str, system: str, temperature: float,
               max_tokens: int, image_data: str, image_mime: str) -> Optional[str]:
    """Attempt a single model call; return result or None on failure."""
    try:
        return OMNI_ENGINE.execute(
            model=model_name,
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            image_b64=image_data,
            image_mime=image_mime,
        )
    except Exception as e:
        print(f"[ai_engine] Model {model_name} failed: {e}, falling back...", file=sys.stderr)
        return None


def generate(
    prompt: str = "",
    system: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    image_data: str = "",
    image_mime: str = "image/jpeg",
    messages: list = None,
    context_text: str = "",
    **kwargs,
) -> str:
    """Generate a response using the OmniKeyEngine rotation system."""

    if messages:
        prompt = _build_prompt(messages, context_text, prompt)

    engine_name = kwargs.get("engine_name")
    if engine_name:
        system, temperature, max_tokens = _apply_engine_config(
            engine_name, system, temperature, max_tokens, kwargs
        )

    cache_key = _get_cache_key(prompt, system, GEMINI_MODELS[0])
    cached = _cache_get(cache_key)
    if cached:
        return cached

    last_err: Optional[Exception] = None
    for round_num in range(MODEL_RETRY_ROUNDS):
        for model_name in GEMINI_MODELS:
            result = _try_model(model_name, prompt, system, temperature,
                                max_tokens, image_data, image_mime)
            if result is not None:
                _cache_set(cache_key, result)
                return result
            last_err = Exception(f"Model {model_name} failed")

        if round_num < MODEL_RETRY_ROUNDS - 1:
            wait = _compute_wait(last_err)
            print(f"[ai_engine] All models exhausted (round {round_num + 1}). "
                  f"Waiting {wait:.0f}s before retry...", file=sys.stderr)
            time.sleep(wait)

    raise last_err or RuntimeError("No Gemini response possible.")


def generate_stream(prompt: str = "", **kwargs) -> Iterator[str]:
    """Yields text in word-by-word chunks for a smooth UI feel."""
    full = generate(prompt=prompt, **kwargs)
    words = full.split(" ")
    chunk = []
    for i, word in enumerate(words):
        chunk.append(word)
        if len(chunk) >= 6 or i == len(words) - 1:
            yield " ".join(chunk) + (" " if i < len(words) - 1 else "")
            chunk = []

# --- System API (Backwards Compatibility) ---
def quick_generate(prompt: str, system: str = "", **kwargs) -> str:
    return generate(prompt=prompt, system=system, max_tokens=2048, **kwargs)

def vision_generate(prompt: str, image_b64: str, mime: str = "image/jpeg", **kwargs) -> str:
    return generate(prompt=prompt, image_data=image_b64, image_mime=mime, **kwargs)

def get_pool_status() -> dict:
    return OMNI_ENGINE.get_status_report()

def get_capacity_summary() -> str:
    s = OMNI_ENGINE.get_status_report()
    return (f"Gemini Engine: {s['available']}/{s['total_keys']} Keys Active | "
            f"Mode: Omnikey v1.0")

def reset_all_keys() -> None:
    OMNI_ENGINE.load_keys()

# Stubs for removed integrations
def stream_chat_with_groq(*args, **kwargs) -> Iterator[str]: 
    return generate_stream(**kwargs)

def chat_with_groq(*args, **kwargs) -> str: 
    return generate(**kwargs)
