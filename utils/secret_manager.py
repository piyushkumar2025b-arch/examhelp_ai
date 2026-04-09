"""
secret_manager.py — Compatibility Shim (v2)
============================================
The 9-key Gemini rotation system has been retired in favour of a single
user-supplied key managed via user_key_store.py.

This module now delegates everything to user_key_store / ai_engine so that
existing callers (app_controller, etc.) continue to work unchanged.

Model aliases are kept for code that imports them directly.
"""

from __future__ import annotations
import sys
from typing import List

# -- Model aliases (kept for backward compat) --
GEMINI_BEST_MODEL  = "gemini-2.5-flash"
GEMINI_FLASH_MODEL = "gemini-2.5-flash"
GEMINI_FAST_MODEL  = "gemini-2.0-flash-lite"


# -- GEMINI_KEYS shim (returns empty list; key now lives in session_state) --
class _EmptyKeyList:
    """Backward-compat stub. Key rotation retired — always empty."""
    def __iter__(self):       return iter([])
    def __len__(self):        return 0
    def __getitem__(self, i): raise IndexError("No keys in rotation (retired)")
    def __bool__(self):       return False

GEMINI_KEYS = _EmptyKeyList()


# -- Public helpers --
def get_gemini_key(index: int = 0) -> str:
    """Return the user's Gemini key from session state (replaces old index lookup)."""
    try:
        from utils.user_key_store import get_user_key
        key, provider = get_user_key()
        if key and provider == "gemini":
            return key
    except Exception:
        pass
    raise RuntimeError(
        "No Gemini key set. Please enter your Gemini API key in the sidebar."
    )


def get_gemini_debug_keys() -> List[str]:
    """Return list with the active key (or empty) for debug display."""
    try:
        key = get_gemini_key()
        return [key]
    except RuntimeError:
        return []


def get_all_gemini_keys() -> List[str]:
    return get_gemini_debug_keys()


def force_reload_keys() -> int:
    """No-op: keys are now in session_state, not loaded from secrets."""
    return len(get_gemini_debug_keys())


def get_load_diagnostics() -> dict:
    return {
        "loaded": True,
        "count": len(get_gemini_debug_keys()),
        "errors": [],
        "note": "Single-key mode (v6) — key from user_key_store",
    }


def validate_all_keys() -> dict:
    diag = get_load_diagnostics()
    return {
        "gemini": {
            "total":       diag["count"],
            "loaded":      diag["count"] > 0,
            "diagnostics": diag,
        }
    }


def call_gemini(prompt: str, system: str = "", model: str = GEMINI_FLASH_MODEL) -> str:
    """Convenience wrapper — delegates to ai_engine."""
    from utils.ai_engine import generate
    return generate(prompt=prompt, system=system)