"""
ai_engine.py — High-Level AI Orchestration
===========================================
Delegates all Gemini operations to the God-Tier OmniKeyEngine.
Maintains backward compatibility for the application's clean API.
"""

from __future__ import annotations
import hashlib
import sys
import threading
from typing import Iterator, Optional, Dict, List
from utils.omnikey_engine import OMNI_ENGINE
from utils.prompts import get_engine_config

# --- Model Selection ---
GEMINI_MODELS = [
    "gemini-2.5-flash",        # Primary - Best working model
    "gemini-2.0-flash",        # Fallback
    "gemini-2.0-flash-lite",   # Minimal
]

# --- Global Cache ---
_mem_cache: Dict[str, str] = {}
_cache_lock = threading.Lock()

def _get_cache_key(prompt: str, system: str, model: str) -> str:
    """Generate a unique hash for caching."""
    h = hashlib.md5(f"{prompt}:{system}:{model}".encode()).hexdigest()
    return h

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
    
    # 1. Message conversion
    if messages:
        turns = []
        if context_text: turns.append(f"Context:\n{context_text}")
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            turns.append(f"{role.capitalize()}: {content}")
        prompt = "\n".join(turns)

    # 2. Engine-specific config injection
    engine_name = kwargs.get("engine_name")
    if engine_name:
        cfg = get_engine_config(engine_name)
        system = (system + "\n\n" if system else "") + cfg["system"]
        temperature = kwargs.get("temperature", cfg["temperature"])
        max_tokens = kwargs.get("max_tokens", cfg["max_tokens"])

    # 3. Cache Check
    cache_key = _get_cache_key(prompt, system, GEMINI_MODELS[0])
    with _cache_lock:
        if cache_key in _mem_cache:
            return _mem_cache[cache_key]

    # 4. Delegate to OmniKeyEngine for the actual call
    # It will automatically handle keys, rotation, and falling back to 2.0 if 2.5 fails
    last_err = None
    for model_name in GEMINI_MODELS:
        try:
            result = OMNI_ENGINE.execute(
                model=model_name,
                prompt=prompt,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens,
                image_b64=image_data,
                image_mime=image_mime
            )
            
            # Cache success
            with _cache_lock:
                if len(_mem_cache) > 500: _mem_cache.clear()
                _mem_cache[cache_key] = result
            return result
        except Exception as e:
            last_err = e
            print(f"[ai_engine] Model {model_name} failed: {str(e)}, falling back...", file=sys.stderr)
            continue

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
