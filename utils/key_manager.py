"""
key_manager.py — Secure, rate-limit-aware Groq API key rotation.

Keys are loaded from environment variables or Streamlit secrets — NEVER hardcoded.

How to configure keys:
  Local dev  → .env file:
    GROQ_API_KEY_1=gsk_...
    GROQ_API_KEY_2=gsk_...   (up to GROQ_API_KEY_8)

  Streamlit Cloud → Advanced Settings → Secrets:
    GROQ_API_KEY_1 = "gsk_..."
    GROQ_API_KEY_2 = "gsk_..."

  Single key → just set GROQ_API_KEY (legacy, still works)
"""

from __future__ import annotations
import os
import time
import threading
from typing import Optional

import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# Load keys securely at import time
# ─────────────────────────────────────────────────────────────────────────────

def _load_keys() -> list[str]:
    keys: list[str] = []

    for i in range(1, 9):
        var = f"GROQ_API_KEY_{i}"
        # Try Streamlit secrets first
        try:
            val = st.secrets.get(var, "")
            if val and val.strip():
                keys.append(val.strip())
                continue
        except Exception:
            pass
        # Fall back to OS env / .env
        val = os.getenv(var, "")
        if val and val.strip():
            keys.append(val.strip())

    # Legacy single-key fallback
    if not keys:
        for var in ("GROQ_API_KEY",):
            try:
                val = st.secrets.get(var, "")
                if val and val.strip():
                    keys.append(val.strip())
                    break
            except Exception:
                pass
            val = os.getenv(var, "")
            if val and val.strip():
                keys.append(val.strip())
                break

    return keys


_RAW_KEYS: list[str] = _load_keys()

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
COOLDOWN_SECONDS: float = 62.0
MAX_RETRIES: int = max(len(_RAW_KEYS) * 2, 2)

# ─────────────────────────────────────────────────────────────────────────────
# Per-key state (module-level — survives Streamlit reruns in same process)
# ─────────────────────────────────────────────────────────────────────────────
_lock = threading.Lock()

_state: dict[str, dict] = {
    k: {"cooldown_until": 0.0, "uses": 0, "errors": 0, "last_used": 0.0}
    for k in _RAW_KEYS
}


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def get_key(override: Optional[str] = None) -> Optional[str]:
    if override and override.strip():
        return override.strip()
    now = time.time()
    with _lock:
        available = [k for k in _RAW_KEYS if _state[k]["cooldown_until"] <= now]
        if available:
            return min(available, key=lambda k: _state[k]["last_used"])
        if _RAW_KEYS:
            return min(_RAW_KEYS, key=lambda k: _state[k]["cooldown_until"])
    return None


def mark_used(key: str) -> None:
    with _lock:
        if key in _state:
            _state[key]["uses"] += 1
            _state[key]["last_used"] = time.time()


def mark_rate_limited(key: str) -> None:
    with _lock:
        if key in _state:
            _state[key]["errors"] += 1
            _state[key]["cooldown_until"] = time.time() + COOLDOWN_SECONDS


def mark_invalid(key: str) -> None:
    with _lock:
        if key in _state:
            _state[key]["errors"] += 1
            _state[key]["cooldown_until"] = time.time() + 86_400 * 365


def seconds_until_available(key: str) -> float:
    with _lock:
        return max(0.0, _state[key]["cooldown_until"] - time.time())


def status_table() -> list[dict]:
    now = time.time()
    rows = []
    with _lock:
        for i, k in enumerate(_RAW_KEYS, 1):
            s = _state[k]
            cd = s["cooldown_until"]
            status = f"⏳ cooldown {cd - now:.0f}s" if cd > now else "✅ available"
            rows.append({"key": f"Key #{i}  ({k[:8]}…{k[-4:]})", "status": status, "uses": s["uses"], "errors": s["errors"]})
    return rows


def reset_all_cooldowns() -> None:
    with _lock:
        for k in _RAW_KEYS:
            _state[k]["cooldown_until"] = 0.0
