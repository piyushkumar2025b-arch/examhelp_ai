"""
secret_manager.py — Gemini-only Key Vault
==========================================
Reads 9 Gemini keys directly from Streamlit Cloud secrets.
NO hardcoded keys. NO .env file. NO Groq. NO other integrations.

In Streamlit Cloud secrets UI, add:
    GEMINI_API_KEY_1 = "AIzaSy..."
    GEMINI_API_KEY_2 = "AIzaSy..."
    ...
    GEMINI_API_KEY_9 = "AIzaSy..."
"""

from __future__ import annotations
import streamlit as st
from typing import List

# ── Models ────────────────────────────────────────────────
GEMINI_BEST_MODEL  = "gemini-2.0-flash"
GEMINI_FLASH_MODEL = "gemini-2.0-flash"
GEMINI_FAST_MODEL  = "gemini-1.5-flash-8b"

# ── Load keys from st.secrets ────────────────────────────
def _load_gemini_keys() -> List[str]:
    keys = []
    for i in range(1, 10):  # slots 1-9
        k = f"GEMINI_API_KEY_{i}"
        try:
            val = st.secrets.get(k, "").strip()
            if val and val.startswith("AIzaSy"):
                keys.append(val)
        except Exception:
            pass
    return keys

GEMINI_KEYS: List[str] = _load_gemini_keys()

# ── Public helpers ────────────────────────────────────────
def get_gemini_key(index: int = 0) -> str:
    """Return key at index (wraps around)."""
    if not GEMINI_KEYS:
        raise RuntimeError(
            "No Gemini keys found. Add GEMINI_API_KEY_1 to GEMINI_API_KEY_9 "
            "in Streamlit Cloud > App settings > Secrets."
        )
    return GEMINI_KEYS[index % len(GEMINI_KEYS)]

def get_gemini_debug_keys() -> List[str]:
    return list(GEMINI_KEYS)

def get_all_gemini_keys() -> List[str]:
    return list(GEMINI_KEYS)

def validate_all_keys() -> dict:
    return {
        "gemini": {
            "total": len(GEMINI_KEYS),
            "loaded": len(GEMINI_KEYS) > 0,
        }
    }

def call_gemini(prompt: str, system: str = "", model: str = GEMINI_FLASH_MODEL) -> str:
    """Convenience wrapper - delegates to ai_engine."""
    from utils.ai_engine import generate
    return generate(prompt=prompt, system=system)
