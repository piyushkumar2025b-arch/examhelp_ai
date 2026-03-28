"""
key_manager.py — Secure, rate-limit-aware Groq API key rotation with full failover.

Keys are loaded from environment variables or Streamlit secrets — NEVER hardcoded.
All 8 keys are kept active and the system automatically switches between them
to ensure uninterrupted output generation.

How to configure keys:
  Local dev  → .env file:
    GROQ_API_KEY_1=gsk_...
    GROQ_API_KEY_2=gsk_...   (up to GROQ_API_KEY_12)

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

    for i in range(1, 13):
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
MAX_RETRIES: int = max(len(_RAW_KEYS) * 2, 4)  # At least 4, or 2× number of keys

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
    """Get the best available key. Returns override if provided, otherwise
    picks the key with the longest time since last use that isn't on cooldown."""
    if override and override.strip():
        return override.strip()
    now = time.time()
    with _lock:
        available = [k for k in _RAW_KEYS if _state[k]["cooldown_until"] <= now]
        if available:
            # Pick the least-recently-used key for best distribution
            return min(available, key=lambda k: _state[k]["last_used"])
        if _RAW_KEYS:
            # All on cooldown — pick the one that comes off soonest
            return min(_RAW_KEYS, key=lambda k: _state[k]["cooldown_until"])
    return None


def get_next_key(exclude_key: Optional[str] = None, override: Optional[str] = None) -> Optional[str]:
    """Get the next available key, excluding a specific key that just failed.
    This is the core of the failover system."""
    if override and override.strip():
        # If using override, can't failover
        return None
    now = time.time()
    with _lock:
        available = [
            k for k in _RAW_KEYS 
            if _state[k]["cooldown_until"] <= now and k != exclude_key
        ]
        if available:
            return min(available, key=lambda k: _state[k]["last_used"])
        # Try keys on cooldown but not the excluded one
        remaining = [k for k in _RAW_KEYS if k != exclude_key]
        if remaining:
            return min(remaining, key=lambda k: _state[k]["cooldown_until"])
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


def total_keys() -> int:
    """Return total number of configured keys."""
    return len(_RAW_KEYS)


def available_keys_count() -> int:
    """Return number of keys not on cooldown."""
    now = time.time()
    with _lock:
        return len([k for k in _RAW_KEYS if _state[k]["cooldown_until"] <= now])


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
