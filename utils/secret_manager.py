"""
secret_manager.py — Gemini Key Vault
======================================
Reads GEMINI_API_KEY_1 … GEMINI_API_KEY_9 from Streamlit secrets.
Keys are loaded LAZILY (on first use) so st.secrets is ready in time.
Includes force-reload and diagnostic logging.
"""

from __future__ import annotations
import os, sys
from typing import List

# ── Model aliases ─────────────────────────────────────
GEMINI_BEST_MODEL  = "gemini-2.0-flash"
GEMINI_FLASH_MODEL = "gemini-2.0-flash"
GEMINI_FAST_MODEL  = "gemini-2.0-flash-lite"

# ── Lazy loader ───────────────────────────────────────
_cached_keys: List[str] = []
_keys_loaded: bool = False
_load_errors: List[str] = []        # track any errors during load


def _load_gemini_keys() -> List[str]:
    """Load keys from Streamlit secrets, with fallback to env vars."""
    global _load_errors
    _load_errors = []
    keys = []

    # ── Method 1: Streamlit secrets (primary — works on Cloud & local) ──
    try:
        import streamlit as st
        for i in range(1, 10):
            k = f"GEMINI_API_KEY_{i}"
            try:
                val = st.secrets.get(k, "").strip()
                if val and val.startswith("AIzaSy"):
                    keys.append(val)
            except Exception as e:
                _load_errors.append(f"st.secrets[{k}]: {e}")
    except Exception as e:
        _load_errors.append(f"Streamlit secrets unavailable: {e}")

    # ── Method 2: Fallback to environment variables ──
    if not keys:
        for i in range(1, 10):
            k = f"GEMINI_API_KEY_{i}"
            val = os.environ.get(k, "").strip()
            if val and val.startswith("AIzaSy"):
                keys.append(val)
        if keys:
            _load_errors.append(f"Loaded {len(keys)} keys from env vars (fallback)")

    if not keys:
        _load_errors.append(
            "ZERO keys found! Add GEMINI_API_KEY_1…9 in "
            ".streamlit/secrets.toml or Streamlit Cloud → App settings → Secrets."
        )
        # Print to stderr so it shows in server logs
        print(f"[secret_manager] WARNING: {_load_errors[-1]}", file=sys.stderr)
    else:
        print(f"[secret_manager] Loaded {len(keys)} Gemini keys successfully.", file=sys.stderr)

    return keys


def _get_keys() -> List[str]:
    """Return keys, loading lazily on first call."""
    global _cached_keys, _keys_loaded
    if not _keys_loaded:
        _cached_keys = _load_gemini_keys()
        _keys_loaded = True
    return _cached_keys


def force_reload_keys() -> int:
    """Force re-read keys from secrets. Returns count of keys loaded."""
    global _cached_keys, _keys_loaded
    _keys_loaded = False
    _cached_keys = []
    keys = _get_keys()
    return len(keys)


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

# ── Public helpers ────────────────────────────────────
def get_gemini_key(index: int = 0) -> str:
    keys = _get_keys()
    if not keys:
        raise RuntimeError(
            "No Gemini keys found. Add GEMINI_API_KEY_1 … GEMINI_API_KEY_9 "
            "in .streamlit/secrets.toml or Streamlit Cloud → App settings → Secrets."
        )
    return keys[index % len(keys)]

def get_gemini_debug_keys() -> List[str]:
    return list(_get_keys())

def get_all_gemini_keys() -> List[str]:
    return list(_get_keys())

def get_load_diagnostics() -> dict:
    """Return diagnostic info about key loading."""
    return {
        "loaded": _keys_loaded,
        "count": len(_cached_keys),
        "errors": list(_load_errors),
    }

def validate_all_keys() -> dict:
    keys = _get_keys()
    return {
        "gemini": {
            "total":  len(keys),
            "loaded": len(keys) > 0,
            "diagnostics": get_load_diagnostics(),
        }
    }

def call_gemini(prompt: str, system: str = "", model: str = GEMINI_FLASH_MODEL) -> str:
    """Convenience wrapper — delegates to ai_engine."""
    from utils.ai_engine import generate
    return generate(prompt=prompt, system=system)