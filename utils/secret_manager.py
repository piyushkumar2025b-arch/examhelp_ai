"""
secret_manager.py — Gemini Key Vault
======================================
Reads GEMINI_API_KEY_1 … GEMINI_API_KEY_9 from Streamlit secrets.
Keys are loaded LAZILY (on first use) so st.secrets is ready in time.
"""

from __future__ import annotations
import streamlit as st
from typing import List

# ── Model aliases ─────────────────────────────────────────
GEMINI_BEST_MODEL  = "gemini-2.0-flash"
GEMINI_FLASH_MODEL = "gemini-2.0-flash"
GEMINI_FAST_MODEL  = "gemini-1.5-flash-8b"

# ── Lazy loader ───────────────────────────────────────────
_cached_keys: List[str] = []
_keys_loaded: bool = False

def _load_gemini_keys() -> List[str]:
    keys = []
    for i in range(1, 10):
        k = f"GEMINI_API_KEY_{i}"
        try:
            val = st.secrets.get(k, "").strip()
            if val and val.startswith("AIzaSy"):
                keys.append(val)
        except Exception:
            pass
    return keys

def _get_keys() -> List[str]:
    """Return keys, loading lazily on first call."""
    global _cached_keys, _keys_loaded
    if not _keys_loaded:
        _cached_keys = _load_gemini_keys()
        _keys_loaded = True
    return _cached_keys

# ── Backwards-compat: GEMINI_KEYS as a lazy property via descriptor ──
class _LazyKeyList:
    """Behaves like a list but loads from st.secrets on first access."""
    def __iter__(self):
        return iter(_get_keys())
    def __len__(self):
        return len(_get_keys())
    def __getitem__(self, idx):
        return _get_keys()[idx]
    def __bool__(self):
        return bool(_get_keys())

GEMINI_KEYS = _LazyKeyList()

# ── Public helpers ────────────────────────────────────────
def get_gemini_key(index: int = 0) -> str:
    keys = _get_keys()
    if not keys:
        raise RuntimeError(
            "No Gemini keys found. Add GEMINI_API_KEY_1 … GEMINI_API_KEY_9 "
            "in Streamlit Cloud → App settings → Secrets."
        )
    return keys[index % len(keys)]

def get_gemini_debug_keys() -> List[str]:
    return list(_get_keys())

def get_all_gemini_keys() -> List[str]:
    return list(_get_keys())

def validate_all_keys() -> dict:
    keys = _get_keys()
    return {
        "gemini": {
            "total":  len(keys),
            "loaded": len(keys) > 0,
        }
    }

def call_gemini(prompt: str, system: str = "", model: str = GEMINI_FLASH_MODEL) -> str:
    """Convenience wrapper — delegates to ai_engine."""
    from utils.ai_engine import generate
    return generate(prompt=prompt, system=system)